"""
Database Module
===============
SQLite baza podataka za korisnike, kvizove i rezultate.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """
    Klasa za upravljanje bazom podataka.
    """
    
    def __init__(self, db_path: str = "quizmaster.db"):
        """
        Inicijalizuje bazu podataka.
        
        Args:
            db_path: Putanja do SQLite baze
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Vraća konekciju sa bazom podataka."""
        conn = sqlite3.connect(self.db_path, timeout=20.0)  # 20 sekundi timeout za lock
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency (Write-Ahead Logging)
        try:
            conn.execute('PRAGMA journal_mode=WAL')
        except:
            pass  # Ignore if WAL is not supported
        return conn
    
    def init_database(self):
        """Kreira tabele ako ne postoje."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela za korisnike
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_quizzes INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                average_accuracy REAL DEFAULT 0.0
            )
        """)
        
        # Tabela za kvizove
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                pdf_filename TEXT,
                pdf_path TEXT,
                num_questions INTEGER DEFAULT 10,
                chunk_size INTEGER DEFAULT 1500,
                topic_keywords TEXT,
                chunks_data TEXT,
                questions_data TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Tabela za rezultate kvizova
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                answers_data TEXT,
                weak_areas TEXT,
                time_taken INTEGER,
                ip_address TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Dodaj ip_address kolonu ako ne postoji
        try:
            cursor.execute("ALTER TABLE quiz_results ADD COLUMN ip_address TEXT")
        except sqlite3.OperationalError:
            pass  # Kolona već postoji
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quizzes_user ON quizzes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_quiz ON quiz_results(quiz_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_user ON quiz_results(user_id)")
        
        conn.commit()
        conn.close()
    
    # User operations
    def create_user(self, username: str, email: str, password_hash: str) -> Optional[int]:
        """Kreira novog korisnika."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Vraća korisnika po korisničkom imenu."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Vraća korisnika po email adresi."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Vraća korisnika po ID-u."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_user_stats(self, user_id: int, score: int, accuracy: float):
        """Ažurira statistike korisnika."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Uzmi trenutne vrednosti
        cursor.execute("SELECT COALESCE(total_quizzes, 0), COALESCE(total_score, 0) FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            total_quizzes = row[0] + 1
            total_score = row[1] + score
            
            # Izračunaj prosečnu tačnost
            cursor.execute("""
                SELECT AVG(accuracy) FROM quiz_results WHERE user_id = ?
            """, (user_id,))
            avg_row = cursor.fetchone()
            avg_accuracy = avg_row[0] if avg_row[0] else 0.0
            
            cursor.execute("""
                UPDATE users 
                SET total_quizzes = ?, total_score = ?, average_accuracy = ?
                WHERE id = ?
            """, (total_quizzes, total_score, avg_accuracy, user_id))
            logger.info(f"Ažurirane statistike korisnika {user_id}: quizzes={total_quizzes}, score={total_score}, accuracy={avg_accuracy}")
        
        conn.commit()
        conn.close()
    
    # Quiz operations
    def create_quiz(
        self,
        user_id: int,
        title: str,
        pdf_filename: str = None,
        pdf_path: str = None,
        num_questions: int = 10,
        chunk_size: int = 1500,
        topic_keywords: str = None,
        chunks_data: List[Dict] = None,
        questions_data: List[Dict] = None,
        status: str = 'draft'
    ) -> Optional[int]:
        """Kreira novi kviz."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        chunks_json = json.dumps(chunks_data) if chunks_data else None
        questions_json = json.dumps(questions_data) if questions_data else None
        
        try:
            cursor.execute("""
                INSERT INTO quizzes (
                    user_id, title, pdf_filename, pdf_path, num_questions,
                    chunk_size, topic_keywords, chunks_data, questions_data, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, title, pdf_filename, pdf_path, num_questions,
                chunk_size, topic_keywords, chunks_json, questions_json, status
            ))
            
            quiz_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Kviz kreiran: {title} (ID: {quiz_id})")
            return quiz_id
        except Exception as e:
            logger.error(f"Greška pri kreiranju kviza: {e}")
            conn.close()
            return None
    
    def get_quiz(self, quiz_id: int) -> Optional[Dict]:
        """Vraća kviz po ID-u."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            quiz = dict(row)
            # Parse JSON polja
            if quiz.get('chunks_data'):
                quiz['chunks_data'] = json.loads(quiz['chunks_data'])
            if quiz.get('questions_data'):
                quiz['questions_data'] = json.loads(quiz['questions_data'])
            return quiz
        return None
    
    def get_user_quizzes(self, user_id: int, status: str = None) -> List[Dict]:
        """Vraća sve kvizove korisnika."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM quizzes 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (user_id, status))
        else:
            cursor.execute("""
                SELECT * FROM quizzes 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        quizzes = []
        for row in rows:
            quiz = dict(row)
            if quiz.get('chunks_data'):
                quiz['chunks_data'] = json.loads(quiz['chunks_data'])
            if quiz.get('questions_data'):
                quiz['questions_data'] = json.loads(quiz['questions_data'])
            quizzes.append(quiz)
        
        return quizzes
    
    def get_public_quizzes(self, exclude_user_id: int = None, limit: int = 50) -> List[Dict]:
        """Vraća javne kvizove drugih korisnika."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if exclude_user_id:
            cursor.execute("""
                SELECT q.*, u.username 
                FROM quizzes q
                JOIN users u ON q.user_id = u.id
                WHERE q.status = 'published' AND q.user_id != ?
                ORDER BY q.created_at DESC
                LIMIT ?
            """, (exclude_user_id, limit))
        else:
            cursor.execute("""
                SELECT q.*, u.username 
                FROM quizzes q
                JOIN users u ON q.user_id = u.id
                WHERE q.status = 'published'
                ORDER BY q.created_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        quizzes = []
        for row in rows:
            quiz = dict(row)
            if quiz.get('chunks_data'):
                quiz['chunks_data'] = json.loads(quiz['chunks_data'])
            if quiz.get('questions_data'):
                quiz['questions_data'] = json.loads(quiz['questions_data'])
            quizzes.append(quiz)
        
        return quizzes
    
    def update_quiz_status(self, quiz_id: int, status: str):
        """Ažurira status kviza."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE quizzes 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, quiz_id))
        conn.commit()
        conn.close()
    
    def update_quiz_questions(self, quiz_id: int, questions_data: List[Dict]):
        """Ažurira pitanja kviza."""
        conn = self.get_connection()
        cursor = conn.cursor()
        questions_json = json.dumps(questions_data)
        cursor.execute("""
            UPDATE quizzes 
            SET questions_data = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (questions_json, quiz_id))
        conn.commit()
        conn.close()
    
    # Result operations
    def save_quiz_result(
        self,
        quiz_id: int,
        user_id: int,
        score: int,
        total_questions: int,
        accuracy: float,
        answers_data: List[Dict],
        weak_areas: List[Tuple[int, float]] = None,
        time_taken: int = None,
        ip_address: str = None
    ) -> Optional[int]:
        """Čuva rezultat kviza."""
        max_retries = 5
        retry_delay = 0.2
        
        for attempt in range(max_retries):
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                answers_json = json.dumps(answers_data)
                weak_areas_json = json.dumps(weak_areas) if weak_areas else None
                
                cursor.execute("""
                    INSERT INTO quiz_results (
                        quiz_id, user_id, score, total_questions, accuracy,
                        answers_data, weak_areas, time_taken, ip_address
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quiz_id, user_id, score, total_questions, accuracy,
                    answers_json, weak_areas_json, time_taken, ip_address
                ))
                
                result_id = cursor.lastrowid
                
                # Ažuriraj statistike korisnika u istoj transakciji
                self._update_user_stats_in_transaction(cursor, user_id, score, accuracy)
                
                conn.commit()
                conn.close()
                logger.info(f"Rezultat sačuvan: Quiz {quiz_id}, User {user_id}, Score {score}/{total_questions}, Accuracy {accuracy}, Result ID {result_id}")
                return result_id
            except sqlite3.OperationalError as e:
                if conn:
                    conn.close()
                if 'locked' in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    logger.error(f"Greška pri čuvanju rezultata (OperationalError): {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return None
            except Exception as e:
                if conn:
                    conn.close()
                logger.error(f"Greška pri čuvanju rezultata: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None
        
        return None
    
    def _update_user_stats_in_transaction(self, cursor, user_id: int, score: int, accuracy: float):
        """Ažurira statistike korisnika unutar postojeće transakcije."""
        # Uzmi trenutne vrednosti
        cursor.execute("SELECT COALESCE(total_quizzes, 0), COALESCE(total_score, 0) FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            total_quizzes = row[0] + 1
            total_score = row[1] + score
            
            # Izračunaj prosečnu tačnost
            cursor.execute("""
                SELECT AVG(accuracy) FROM quiz_results WHERE user_id = ?
            """, (user_id,))
            avg_row = cursor.fetchone()
            avg_accuracy = avg_row[0] if avg_row[0] else 0.0
            
            cursor.execute("""
                UPDATE users 
                SET total_quizzes = ?, total_score = ?, average_accuracy = ?
                WHERE id = ?
            """, (total_quizzes, total_score, avg_accuracy, user_id))
            logger.info(f"Ažurirane statistike korisnika {user_id}: quizzes={total_quizzes}, score={total_score}, accuracy={avg_accuracy}")
    
    def get_quiz_results(self, quiz_id: int) -> List[Dict]:
        """Vraća sve rezultate za kviz."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, u.username, u.email
            FROM quiz_results r
            JOIN users u ON r.user_id = u.id
            WHERE r.quiz_id = ?
            ORDER BY r.completed_at DESC
        """, (quiz_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            if result.get('answers_data'):
                try:
                    result['answers_data'] = json.loads(result['answers_data'])
                except:
                    pass
            if result.get('weak_areas'):
                try:
                    result['weak_areas'] = json.loads(result['weak_areas'])
                except:
                    pass
            results.append(result)
        
        logger.info(f"get_quiz_results returned {len(results)} results for quiz {quiz_id}")
        return results
    
    def get_user_results(self, user_id: int) -> List[Dict]:
        """Vraća sve rezultate korisnika."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, q.title as quiz_title
            FROM quiz_results r
            JOIN quizzes q ON r.quiz_id = q.id
            WHERE r.user_id = ?
            ORDER BY r.completed_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            if result.get('answers_data'):
                result['answers_data'] = json.loads(result['answers_data'])
            if result.get('weak_areas'):
                result['weak_areas'] = json.loads(result['weak_areas'])
            results.append(result)
        
        return results
    
    # Leaderboard operations
    def get_leaderboard(self, limit: int = 100) -> List[Dict]:
        """Vraća leaderboard sa najboljim korisnicima."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id, username, total_quizzes, total_score, average_accuracy,
                (COALESCE(total_score, 0) * COALESCE(average_accuracy, 0)) as leaderboard_score
            FROM users
            WHERE COALESCE(total_quizzes, 0) > 0
            ORDER BY leaderboard_score DESC, average_accuracy DESC, total_score DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = [dict(row) for row in rows]
        logger.info(f"Leaderboard query returned {len(result)} users")
        return result
