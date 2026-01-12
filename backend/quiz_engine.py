"""
Quiz Engine Module
==================
Modul za upravljanje kvizom, praćenje napretka i koordinaciju komponenti.
"""

from typing import List, Dict, Optional, Tuple
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizEngine:
    """
    Glavna klasa za upravljanje kvizom.
    Koordinira RL agenta, generator pitanja i praćenje napretka.
    """
    
    def __init__(
        self,
        chunks: List[Dict[str, any]],
        question_generator,
        rl_agent,
        total_questions: int = 10
    ):
        """
        Inicijalizuje kviz engine.
        
        Args:
            chunks: Lista chunk-ova iz PDF-a
            question_generator: Instanca QuestionGenerator
            rl_agent: Instanca RLAgent
            total_questions: Ukupan broj pitanja u kvizu
        """
        self.chunks = chunks
        self.question_generator = question_generator
        self.rl_agent = rl_agent
        self.total_questions = total_questions
        
        # Cache za generisana pitanja
        self.questions_cache = {}  # chunk_id -> lista pitanja
        
        # Stanje kviza
        self.current_question_index = 0
        self.questions_answered = []
        self.score = 0
        self.current_question = None
        
        # Generiši početna pitanja
        self._initialize_questions()
    
    def _initialize_questions(self):
        """Inicijalizuje početna pitanja iz različitih chunk-ova."""
        logger.info(f"Inicijalizovanje kviza sa {len(self.chunks)} chunk-ova...")
        
        # Generiši po jedno pitanje iz svakog chunk-a za početak
        chunks_to_init = min(5, len(self.chunks))  # Prvih 5 chunk-ova
        successful_chunks = 0
        
        for chunk in self.chunks[:chunks_to_init]:
            chunk_id = chunk.get('chunk_id', self.chunks.index(chunk))
            if chunk_id not in self.questions_cache:
                try:
                    questions = self.question_generator.generate_questions_from_chunk(
                        chunk, 
                        num_questions=2,
                        difficulty='medium'
                    )
                    if questions:
                        self.questions_cache[chunk_id] = questions
                        successful_chunks += 1
                        logger.info(f"Uspešno generisano {len(questions)} pitanja za chunk {chunk_id}")
                    else:
                        logger.warning(f"Nema generisanih pitanja za chunk {chunk_id}")
                except Exception as e:
                    logger.error(f"Greška pri generisanju pitanja za chunk {chunk_id}: {e}")
                    # Continue with other chunks
                    continue
        
        if successful_chunks == 0:
            logger.error("Nije moguće generisati pitanja ni iz jednog chunk-a! Proverite API key.")
        else:
            logger.info(f"Uspešno inicijalizovano {successful_chunks}/{chunks_to_init} chunk-ova")
    
    def get_next_question(self) -> Optional[Dict[str, any]]:
        """
        Vraća sledeće pitanje na osnovu RL agenta.
        
        Returns:
            Rečnik sa pitanjem ili None ako je kviz završen
        """
        if self.current_question_index >= self.total_questions:
            return None
        
        # Izaberi chunk na osnovu RL agenta
        available_chunks = list(range(len(self.chunks)))
        selected_chunk_id = self.rl_agent.select_chunk(available_chunks)
        selected_chunk = self.chunks[selected_chunk_id]
        
        # Proveri da li ima pitanja u cache-u
        if selected_chunk_id not in self.questions_cache or not self.questions_cache[selected_chunk_id]:
            # Generiši nova pitanja
            difficulty = self.rl_agent.select_question_difficulty(selected_chunk_id)
            try:
                questions = self.question_generator.generate_questions_from_chunk(
                    selected_chunk,
                    num_questions=3,
                    difficulty=difficulty
                )
                if questions:
                    self.questions_cache[selected_chunk_id] = questions
                else:
                    logger.warning(f"Nema generisanih pitanja za chunk {selected_chunk_id}, pokušavam sledeći chunk")
                    # Try next chunk
                    if self.current_question_index < self.total_questions - 1:
                        return self.get_next_question()
                    else:
                        return None
            except ValueError as e:
                # API key or permission error - propagate up
                logger.error(f"API greška pri generisanju pitanja: {e}")
                raise e
            except Exception as e:
                logger.error(f"Greška pri generisanju pitanja za chunk {selected_chunk_id}: {e}")
                # Try next chunk
                if self.current_question_index < self.total_questions - 1:
                    return self.get_next_question()
                else:
                    return None
        
        # Izaberi nasumično pitanje iz cache-a
        available_questions = self.questions_cache.get(selected_chunk_id, [])
        if not available_questions:
            logger.warning(f"Nema pitanja u cache-u za chunk {selected_chunk_id}")
            # Try next chunk
            if self.current_question_index < self.total_questions - 1:
                return self.get_next_question()
            else:
                return None
        
        question = random.choice(available_questions)
        question['question_index'] = self.current_question_index
        question['total_questions'] = self.total_questions
        
        self.current_question = question
        return question
    
    def submit_answer(self, user_answer: str) -> Dict[str, any]:
        """
        Procesira odgovor korisnika.
        
        Args:
            user_answer: Odgovor korisnika ('A', 'B', 'C', ili 'D')
            
        Returns:
            Rečnik sa rezultatom i objašnjenjem
        """
        if not self.current_question:
            return {'error': 'Nema aktivnog pitanja'}
        
        # Normalizuj odgovor
        user_answer = user_answer.upper().strip()
        correct_answer = self.current_question['correct_answer'].upper().strip()
        
        is_correct = user_answer == correct_answer
        
        # Ažuriraj score
        if is_correct:
            self.score += 1
        
        # Ažuriraj RL agenta
        chunk_id = self.current_question['chunk_id']
        difficulty = 0.5  # Može se izvući iz pitanja ako je sačuvano
        self.rl_agent.update_state(chunk_id, is_correct, difficulty)
        
        # Generiši objašnjenje
        explanation = self.question_generator.generate_explanation(
            self.current_question,
            user_answer,
            is_correct
        )
        
        # Sačuvaj odgovor
        result = {
            'is_correct': is_correct,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'explanation': explanation,
            'score': self.score,
            'total_answered': self.current_question_index + 1,
            'accuracy': self.score / (self.current_question_index + 1) if (self.current_question_index + 1) > 0 else 0
        }
        
        self.questions_answered.append({
            'question': self.current_question,
            'user_answer': user_answer,
            'result': result
        })
        
        self.current_question_index += 1
        self.current_question = None
        
        return result
    
    def get_progress(self) -> Dict[str, any]:
        """
        Vraća trenutni napredak kviza.
        
        Returns:
            Rečnik sa statistikama napretka
        """
        stats = self.rl_agent.get_statistics()
        
        return {
            'questions_answered': self.current_question_index,
            'total_questions': self.total_questions,
            'score': self.score,
            'accuracy': self.score / self.current_question_index if self.current_question_index > 0 else 0,
            'rl_statistics': stats,
            'progress_percentage': (self.current_question_index / self.total_questions) * 100 if self.total_questions > 0 else 0
        }
    
    def is_complete(self) -> bool:
        """Proverava da li je kviz završen."""
        return self.current_question_index >= self.total_questions
    
    def get_final_report(self) -> Dict[str, any]:
        """
        Generiše finalni izveštaj nakon završetka kviza.
        
        Returns:
            Rečnik sa finalnim statistikama
        """
        progress = self.get_progress()
        stats = self.rl_agent.get_statistics()
        
        return {
            'total_questions': self.total_questions,
            'score': self.score,
            'accuracy': progress['accuracy'],
            'weak_areas': stats['weak_areas'],
            'chunks_covered': stats['chunks_covered'],
            'questions_by_chunk': self._get_questions_by_chunk()
        }
    
    def _get_questions_by_chunk(self) -> Dict[int, int]:
        """Vraća broj pitanja po chunk-u."""
        chunk_counts = {}
        for qa in self.questions_answered:
            chunk_id = qa['question']['chunk_id']
            chunk_counts[chunk_id] = chunk_counts.get(chunk_id, 0) + 1
        return chunk_counts

