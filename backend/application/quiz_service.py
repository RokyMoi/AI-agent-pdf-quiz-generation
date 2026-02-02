"""
Quiz service: orkestracija poslovne logike (chunking, LLM pozivi, tok rada).
Sadrži jasne entry-point funkcije koje web sloj poziva.
"""

import logging
from google_gemini_generator import GeminiQuestionGenerator
from rl_agent import RLAgent
from quiz_engine import QuizEngine

logger = logging.getLogger(__name__)


class QuizService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def _ensure_generator(self):
        api_key = self.api_key or __import__('os').environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError('GOOGLE_API_KEY nije postavljen')
        return GeminiQuestionGenerator(api_key=api_key)

    def generate_question_from_chunk(self, chunk: dict, difficulty: str = 'medium', question_number: int = 1):
        gen = self._ensure_generator()
        questions = gen.generate_questions_from_chunk(chunk, num_questions=1, difficulty=difficulty)
        if not questions:
            raise RuntimeError('Nije moguće generisati pitanje iz chunk-a')
        q = questions[0]
        q['question_number'] = question_number
        return q

    def generate_questions(self, chunks: list, num_questions: int = 10, topic_keywords: str = ''):
        gen = self._ensure_generator()
        rl_agent = RLAgent(num_chunks=len(chunks))
        quiz_engine = QuizEngine(
            chunks=chunks,
            question_generator=gen,
            rl_agent=rl_agent,
            total_questions=num_questions
        )
        questions = []
        max_attempts = min(num_questions * 2, len(chunks) * 3)
        for i in range(max_attempts):
            try:
                question = quiz_engine.get_next_question()
                if question and question.get('question'):
                    questions.append(question)
                if len(questions) >= num_questions:
                    break
            except Exception as e:
                logger.warning(f"generate_questions: attempt {i+1} failed: {e}")
                continue
        if not questions:
            raise RuntimeError('Nije moguće generisati pitanja')
        return questions

    def process_job(self, job):
        """Procesira jedan job prema tipu. Ovo je centralna tačka za background worker."""
        job_type = job.job_type
        payload = job.payload or {}
        if job_type == 'generate_next_question':
            # payload expected: {'session_id': int, 'chunks': [...], 'num_questions': int}
            session_id = payload.get('session_id')
            chunks = payload.get('chunks', [])
            num_questions = payload.get('num_questions', 1)
            # For background jobs, just generate questions and persist
            questions = self.generate_questions(chunks=chunks, num_questions=num_questions)
            # return result for job store
            return {'questions': questions}
        elif job_type == 'parse_and_chunk':
            # payload expected: {'tmp_path': str, 'chunk_size': int, 'topic_keywords': str, 'quiz_title': str, 'num_questions': int, 'user_id': int}
            from .upload_service import UploadService
            from infra.job_queue import JobQueue

            tmp_path = payload.get('tmp_path')
            chunk_size = int(payload.get('chunk_size', 1500))
            topic_keywords = payload.get('topic_keywords', '')
            quiz_title = payload.get('quiz_title', 'Untitled Quiz')
            num_questions = int(payload.get('num_questions', 10))
            user_id = payload.get('user_id')

            upload_service = UploadService()
            result = upload_service.parse_and_chunk_pdf(
                tmp_path=tmp_path,
                chunk_size=chunk_size,
                topic_keywords=topic_keywords,
                quiz_title=quiz_title,
                num_questions=num_questions,
                user_id=user_id
            )

            # Optionally enqueue generate questions job for the created quiz
            chunks = result.get('chunks', [])
            if chunks:
                q = JobQueue()
                gen_job_id = q.create_job('generate_next_question', payload={'chunks': chunks, 'num_questions': num_questions})
                result['enqueued_generate_job_id'] = gen_job_id

            return result
        else:
            raise NotImplementedError(f'Unknown job type: {job_type}')
