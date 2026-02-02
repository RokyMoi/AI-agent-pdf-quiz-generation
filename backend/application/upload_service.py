"""
Upload service: premješta parsing i chunking logic iz web sloja u servisni sloj.
Funkcija `parse_and_chunk_pdf` parsira PDF, chunk-uje, te kreira `quiz` u bazi (status='processing').
"""

import logging
import os
from core.pdf_parser import PDFParser
from core.chunking import TextChunker
from database import Database

logger = logging.getLogger(__name__)


class UploadService:
    def __init__(self, db: Database = None):
        self.db = db or Database()

    def parse_and_chunk_pdf(self, tmp_path: str, chunk_size: int = 1500, topic_keywords: str = '', quiz_title: str = 'Untitled Quiz', num_questions: int = 10, user_id: int = None):
        """Parsiraj PDF i kreiraj kviz (sa chunk-ovima) u bazi.

        Vraća dict: {'quiz_id': int, 'num_chunks': int, 'chunks': [...], 'message': str}
        """
        if not os.path.exists(tmp_path):
            raise FileNotFoundError('Temp PDF file not found')

        # Parse PDF
        parser = PDFParser()
        text = parser.extract_text(tmp_path)
        if not text or len(text.strip()) < 100:
            raise RuntimeError('PDF nije parsiran ili je prazan')

        # Chunking
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=200)
        chunks = chunker.chunk_text(text, method='words')

        # Filter by topic if provided
        if topic_keywords:
            keywords = [kw.strip() for kw in topic_keywords.split(',')]
            chunks = chunker.filter_chunks_by_topic(chunks, keywords)

        if not chunks:
            raise RuntimeError('Nisu pronađeni relevantni segmenti u PDF-u')

        # Persist quiz with chunks (status 'processing')
        quiz_id = self.db.create_quiz(
            user_id=user_id or 0,
            title=quiz_title,
            pdf_filename=os.path.basename(tmp_path),
            pdf_path=tmp_path,
            num_questions=num_questions,
            chunks_data=chunks,
            status='processing'
        )

        logger.info(f'Parsed PDF and created quiz id={quiz_id} with {len(chunks)} chunks')
        return {
            'quiz_id': quiz_id,
            'num_chunks': len(chunks),
            'chunks': chunks,
            'message': f'PDF parsed and {len(chunks)} chunks created',
        }
