"""
Question Generator Module
=========================
Modul za generisanje pitanja iz PDF segmenata koristeći Claude LLM.
"""

import anthropic
import json
import re
from typing import List, Dict, Optional
import logging
import os
from dotenv import load_dotenv

# Učitaj environment varijable iz .env fajla (ako postoji i nije korumpiran)
try:
    load_dotenv()
except Exception as e:
    # If .env is corrupted or can't be read, continue without it
    logging.warning(f"Ne mogu da učitam .env fajl: {e}. Nastavljam bez .env fajla.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Klasa za generisanje pitanja koristeći Claude API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicijalizuje generator pitanja.
        
        Args:
            api_key: Claude API ključ (može biti u env varijabli ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nije postavljen. Postavite ga u .env fajlu ili kao argument.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"  # Koristi Haiku za brže i jeftinije generisanje
    
    def generate_questions_from_chunk(
        self, 
        chunk: Dict[str, any], 
        num_questions: int = 3,
        difficulty: str = "medium"
    ) -> List[Dict[str, any]]:
        """
        Generiše pitanja iz jednog chunk-a.
        
        Args:
            chunk: Rečnik sa tekstom chunk-a i metapodacima
            num_questions: Broj pitanja za generisanje
            difficulty: Težina pitanja ('easy', 'medium', 'hard')
            
        Returns:
            Lista rečnika sa pitanjima
        """
        text = chunk['text']
        chunk_id = chunk.get('chunk_id', 0)
        title = chunk.get('title', f"Segment {chunk_id}")
        
        # Ograniči dužinu teksta ako je previše dugačak
        max_chars = 8000  # Claude ima limit na kontekst
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            logger.warning(f"Tekst chunk-a {chunk_id} je skraćen na {max_chars} karaktera")
        
        prompt = self._create_question_prompt(text, num_questions, difficulty)
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            questions = self._parse_questions(response_text, chunk_id, title)
            
            logger.info(f"Generisano {len(questions)} pitanja iz chunk-a {chunk_id}")
            return questions
            
        except Exception as e:
            logger.error(f"Greška pri generisanju pitanja: {e}")
            return []
    
    def _create_question_prompt(self, text: str, num_questions: int, difficulty: str) -> str:
        """Kreira prompt za generisanje pitanja."""
        difficulty_instructions = {
            'easy': 'Osnovna činjenice i direktne informacije iz teksta.',
            'medium': 'Srednje teškoće, zahteva razumevanje konteksta i povezivanje ideja.',
            'hard': 'Kompleksna pitanja koja zahtevaju dubinsko razumevanje, analizu i sintezu informacija.'
        }
        
        prompt = f"""Generiši {num_questions} multiple-choice pitanja iz sledećeg teksta.

Težina pitanja: {difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}

Tekst:
{text}

Za svako pitanje generiši:
1. Tekst pitanja (jasno i precizno)
2. 4 opcije odgovora (A, B, C, D)
3. Tačan odgovor (A, B, C ili D)
4. Kratko objašnjenje zašto je odgovor tačan

Formatiraj odgovor kao JSON listu sa sledećom strukturom:
[
  {{
    "question": "Tekst pitanja",
    "options": {{
      "A": "Opcija A",
      "B": "Opcija B",
      "C": "Opcija C",
      "D": "Opcija D"
    }},
    "correct_answer": "A",
    "explanation": "Objašnjenje zašto je odgovor tačan"
  }}
]

Generiši tačno {num_questions} pitanja. Odgovori SAMO sa JSON objektom, bez dodatnog teksta."""
        
        return prompt
    
    def _parse_questions(self, response_text: str, chunk_id: int, title: str) -> List[Dict[str, any]]:
        """Parsira odgovor od Claude-a u strukturu pitanja."""
        questions = []
        
        # Pokušaj da ekstraktuje JSON iz odgovora
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            try:
                questions_data = json.loads(json_match.group())
                
                for i, q_data in enumerate(questions_data):
                    question = {
                        'question_id': f"{chunk_id}_{i}",
                        'chunk_id': chunk_id,
                        'chunk_title': title,
                        'question': q_data.get('question', ''),
                        'options': q_data.get('options', {}),
                        'correct_answer': q_data.get('correct_answer', ''),
                        'explanation': q_data.get('explanation', ''),
                        'difficulty': 'medium'  # Može se dodati u prompt
                    }
                    questions.append(question)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Greška pri parsiranju JSON-a: {e}")
                logger.debug(f"Response text: {response_text[:500]}")
        
        return questions
    
    def generate_explanation(
        self, 
        question: Dict[str, any], 
        user_answer: str, 
        is_correct: bool
    ) -> str:
        """
        Generiše detaljno objašnjenje za odgovor korisnika.
        
        Args:
            question: Rečnik sa pitanjem
            user_answer: Odgovor korisnika
            is_correct: Da li je odgovor tačan
            
        Returns:
            String sa objašnjenjem
        """
        prompt = f"""Korisnik je odgovorio na sledeće pitanje:

Pitanje: {question['question']}
Opcije:
A: {question['options'].get('A', '')}
B: {question['options'].get('B', '')}
C: {question['options'].get('C', '')}
D: {question['options'].get('D', '')}

Korisnikov odgovor: {user_answer}
Tačan odgovor: {question['correct_answer']}
Korisnikov odgovor je {'tačan' if is_correct else 'netačan'}.

Generiši detaljno, edukativno objašnjenje koje:
1. Objašnjava zašto je tačan odgovor tačan
2. Objašnjava zašto su ostale opcije netačne (ako je relevantno)
3. Pruža dodatni kontekst i povezane informacije
4. Pomaže korisniku da bolje razume koncept

Budi jasno, prijateljski i edukativan."""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Greška pri generisanju objašnjenja: {e}")
            return question.get('explanation', 'Nema objašnjenja.')

