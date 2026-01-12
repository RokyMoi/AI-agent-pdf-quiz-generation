"""
Google Gemini Question Generator
=================================
Alternativni generator pitanja koristeći Google Gemini API.
"""

import google.generativeai as genai
import json
import re
from typing import List, Dict, Optional
import logging
import os
import time

# Try to load .env, but don't fail if it doesn't exist or is corrupted
try:
    from dotenv import load_dotenv
    try:
        load_dotenv()
    except Exception as e:
        # If .env is corrupted or can't be read, continue without it
        logging.warning(f"Ne mogu da učitam .env fajl: {e}. Koristiću default API key.")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiQuestionGenerator:
    """
    Klasa za generisanje pitanja koristeći Google Gemini API.
    
    Koristi najnovije Gemini modele prema Google dokumentaciji:
    https://ai.google.dev/gemini-api/docs/models
    
    Prioritet modela (prema rate limitima na free tieru):
    1. gemini-2.5-flash-lite - 10 RPM, 250K TPM, 20 RPD (NAJVIŠI RPM!)
    2. gemini-2.0-flash-lite - verovatno 10 RPM (slično kao 2.5-flash-lite)
    3. gemini-2.5-flash - 5 RPM, 250K TPM, 20 RPD (dobar price-performance)
    4. gemini-2.0-flash - 5 RPM (prethodna generacija)
    5. gemini-2.5-pro - Pro model za kompleksnije zadatke
    6. gemini-1.5-flash - stariji model (fallback)
    7. gemini-1.5-pro - stariji model (fallback)
    
    Rate limiti (free tier):
    - Flash-Lite: 10 RPM (6 sekundi delay između zahteva)
    - Standard Flash: 5 RPM (12 sekundi delay između zahteva)
    - TPM: 250K tokena po minuti za Flash modele
    - RPD: 20 zahteva po danu za Flash modele
    
    Automatski delay između zahteva da izbegne prekoračenje rate limita.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicijalizuje generator pitanja sa Gemini.
        
        Args:
            api_key: Google API ključ
        """
        # Lista Google Gemini API ključeva za rotaciju (rezervni ključevi)
        # NOTE: Samo Google Gemini API ključevi su podržani
        primary_key = api_key or os.getenv('GOOGLE_API_KEY') or "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
        self.api_keys = [
            primary_key,  # Default/primary key
            # Dodajte ovde rezervne Google Gemini API ključeve ako ih imate
            # Primer: "AIzaSy...", "AIzaSy..." itd.
        ]
        
        # Index trenutnog API ključa
        self.current_api_key_index = 0
        self.api_key = self.api_keys[self.current_api_key_index]
        
        if not api_key and not os.getenv('GOOGLE_API_KEY'):
            os.environ['GOOGLE_API_KEY'] = self.api_key
            logger.info(f"Koristim default GOOGLE_API_KEY (ključ {self.current_api_key_index + 1}/{len(self.api_keys)})")
        else:
            logger.info(f"Koristim API ključ {self.current_api_key_index + 1}/{len(self.api_keys)}")
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Try models in order based on Google Gemini API documentation:
            # https://ai.google.dev/gemini-api/docs/models
            # Priority: Latest 2.5 and 2.0 models first
            # NOTE: Using exact model names from official documentation
            
            # Prema rate limitima na free tieru (prema Google AI Studio):
            # gemini-2.5-flash-lite: 10 RPM, 250K TPM, 20 RPD (NAJVIŠE RPM!)
            # gemini-2.5-flash: 5 RPM, 250K TPM, 20 RPD
            # gemini-2.0-flash-lite: verovatno 10 RPM (slično kao 2.5-flash-lite)
            # Gemma modeli: 30 RPM ali nisu za generisanje pitanja (drugačiji use case)
            self.models_to_try = [
                # Flash-Lite modeli prvo - NAJVIŠI RPM limiti na free tieru (10 RPM vs 5 RPM)
                ('gemini-2.5-flash-lite', '10 RPM, 250K TPM, 20 RPD - NAJVIŠI RPM limit na free tieru'),
                ('gemini-2.0-flash-lite', 'verovatno 10 RPM - optimizovan za cost efficiency'),
                # Standard Flash modeli (5 RPM limit)
                ('gemini-2.5-flash', '5 RPM, 250K TPM, 20 RPD - dobar price-performance'),
                ('gemini-2.0-flash', '5 RPM - prethodna generacija Flash'),
                # Pro modeli (obično niži RPM limiti)
                ('gemini-2.5-pro', 'najnoviji Pro model za kompleksnije zadatke'),
                # Fallback na starije modele
                ('gemini-1.5-flash', 'stariji model - fallback opcija'),
                ('gemini-1.5-pro', 'stariji model - fallback opcija')
            ]
            
            # Index trenutnog modela u listi (za automatski fallback)
            self.current_model_index = 0
            
            # Inicijalizuj prvi model
            self._initialize_model()
                
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Greška pri konfigurisanju Gemini API: {e}")
            raise ValueError(f"Ne mogu da se povežem sa Google Gemini API. Proverite API key: {str(e)}")
        
        # Rate limiting prema Google AI Studio rate limitima:
        # gemini-2.5-flash-lite: 10 RPM (6 sekundi delay)
        # gemini-2.5-flash: 5 RPM (12 sekundi delay)
        # Source: https://ai.google.dev/gemini-api/docs/rate-limits
        self.last_request_time = 0
        # Početni delay - biće prilagođen prema modelu koji se koristi
        # Flash-Lite: 6 sekundi (10 RPM), Standard Flash: 12 sekundi (5 RPM)
        self.min_request_delay = 6.0  # Početni delay za Flash-Lite (10 RPM)
    
    def _initialize_model(self):
        """Inicijalizuje trenutni model iz liste."""
        last_error = None
        
        # Pokušaj sa trenutnim modelom i svim sledećim
        for i in range(self.current_model_index, len(self.models_to_try)):
            model_name, description = self.models_to_try[i]
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"✓ Koristim {model_name} model ({description})")
                
                # Prilagodi delay prema modelu
                if 'flash-lite' in model_name:
                    self.min_request_delay = 6.0  # 10 RPM = 6 sekundi delay
                    logger.info(f"Rate limit za {model_name}: 10 RPM (delay: 6s)")
                elif 'flash' in model_name:
                    self.min_request_delay = 12.0  # 5 RPM = 12 sekundi delay
                    logger.info(f"Rate limit za {model_name}: 5 RPM (delay: 12s)")
                else:
                    self.min_request_delay = 12.0  # Default za Pro modele
                    logger.info(f"Rate limit za {model_name}: 5 RPM (delay: 12s)")
                
                self.current_model_index = i
                return  # Model initialized successfully
                
            except Exception as e:
                last_error = e
                logger.warning(f"{model_name} nije dostupan: {e}")
                continue
        
        # If we get here, all remaining models failed
        raise ValueError(f"Ne mogu da se povežem sa Google Gemini API. Svi preostali modeli su neuspešni. Poslednja greška: {str(last_error)}")
    
    def _try_next_model(self, error_msg: str):
        """Pokušava da pređe na sledeći model u listi kada se desi greška."""
        if self.current_model_index >= len(self.models_to_try) - 1:
            # Nema više modela za pokušavanje
            logger.error("Svi modeli su iscrpljeni. Nema više opcija za fallback.")
            return False
        
        logger.warning(f"Greška sa trenutnim modelom: {error_msg[:200]}")
        logger.info(f"Prelazim na sledeći model u listi...")
        
        self.current_model_index += 1
        try:
            self._initialize_model()
            logger.info(f"✓ Uspešno prešao na novi model")
            return True
        except Exception as e:
            logger.error(f"Ne mogu da inicijalizujem sledeći model: {e}")
            return False
    
    def generate_questions_from_chunk(
        self,
        chunk: Dict[str, any],
        num_questions: int = 3,
        difficulty: str = "medium"
    ) -> List[Dict[str, any]]:
        """
        Generiše pitanja iz chunk-a koristeći Gemini.
        
        Args:
            chunk: Chunk sa tekstom
            num_questions: Broj pitanja
            difficulty: Težina
            
        Returns:
            Lista pitanja
        """
        text = chunk['text']
        chunk_id = chunk.get('chunk_id', 0)
        title = chunk.get('title', f"Segment {chunk_id}")
        
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        prompt = self._create_question_prompt(text, num_questions, difficulty)
        
        try:
            # Rate limiting: Wait if needed to avoid exceeding free tier limits
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_delay:
                wait_time = self.min_request_delay - time_since_last_request
                logger.info(f"Rate limiting: čekam {wait_time:.1f}s pre sledećeg zahteva...")
                time.sleep(wait_time)
            
            model_name = self.models_to_try[self.current_model_index][0]
            logger.info(f"Pozivanje Gemini API za chunk {chunk_id} (model: {model_name})...")
            self.last_request_time = time.time()
            
            # Generiši pitanje sa timeout-om (koristi threading za timeout)
            import threading
            response_result = [None]
            response_error = [None]
            
            def api_call():
                try:
                    response_result[0] = self.model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.7,
                            'top_p': 0.8,
                            'top_k': 40,
                            'max_output_tokens': 2048,
                        }
                    )
                except Exception as e:
                    response_error[0] = e
            
            # Pokreni API poziv u thread-u
            api_thread = threading.Thread(target=api_call)
            api_thread.daemon = True
            api_thread.start()
            api_thread.join(timeout=45)  # 45 sekundi timeout
            
            if api_thread.is_alive():
                logger.error(f"Gemini API timeout za chunk {chunk_id} (model: {model_name})")
                raise TimeoutError(f"API zahtev je prekoračio vreme čekanja (45 sekundi). Model: {model_name}")
            
            if response_error[0]:
                raise response_error[0]
            
            response = response_result[0]
            
            if not response or not hasattr(response, 'text'):
                logger.error(f"Gemini API nije vratio tekst za chunk {chunk_id}")
                return []
            
            response_text = response.text
            logger.info(f"Gemini API odgovor primljen (dužina: {len(response_text)} karaktera)")
            
            questions = self._parse_questions(response_text, chunk_id, title)
            
            if not questions:
                logger.warning(f"Nije moguće parsirati pitanja iz Gemini odgovora za chunk {chunk_id}")
                logger.debug(f"Gemini odgovor: {response_text[:500]}")
            
            logger.info(f"Generisano {len(questions)} pitanja sa Gemini iz chunk-a {chunk_id}")
            return questions
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Greška pri generisanju pitanja sa Gemini za chunk {chunk_id}: {error_msg}")
            
            # Check for specific API errors that should trigger model fallback
            should_try_next_model = False
            
            if '429' in error_msg or 'QUOTA' in error_msg.upper() or 'RATE_LIMIT' in error_msg.upper() or 'exceeded' in error_msg.lower():
                # Rate limit - pokušaj sledeći model
                logger.warning(f"Rate limit prekoračen. Pokušavam sledeći model...")
                should_try_next_model = True
            elif '404' in error_msg or 'NOT_FOUND' in error_msg.upper() or ('model' in error_msg.lower() and 'not found' in error_msg.lower()):
                # Model not found - pokušaj sledeći model
                logger.warning(f"Model nije dostupan (404). Pokušavam sledeći model...")
                should_try_next_model = True
            elif 'PERMISSION' in error_msg.upper() or 'FORBIDDEN' in error_msg.upper():
                # Permission error - pokušaj sledeći model
                logger.warning(f"Permission greška. Pokušavam sledeći model...")
                should_try_next_model = True
            
            # Pokušaj sledeći Gemini model (NE koristi OpenAI automatski!)
            if should_try_next_model:
                if self._try_next_model(error_msg):
                    # Retry sa novim Gemini modelom
                    logger.info(f"Ponovo pokušavam generisanje pitanja sa novim Gemini modelom...")
                    return self.generate_questions_from_chunk(chunk, num_questions, difficulty)
                else:
                    # Nema više Gemini modela - vrati grešku (NE prelazi na OpenAI automatski!)
                    logger.error("Svi Gemini modeli su iscrpljeni. Nema više opcija za fallback.")
                    raise ValueError(f"API kvota prekoračena ili model nije dostupan. Pokušali smo sve dostupne Gemini modele. Detalji: {error_msg[:200]}")
            
            # Za ostale greške (API key, itd.) - ne pokušavaj fallback
            if 'API_KEY' in error_msg.upper() or 'AUTHENTICATION' in error_msg.upper():
                raise ValueError(f"API key greška: {error_msg}. Proverite GOOGLE_API_KEY.")
            else:
                logger.error(f"Detalji greške: {type(e).__name__}: {error_msg}")
                # Don't return empty list, raise error so it can be caught upstream
                raise ValueError(f"Greška pri generisanju pitanja: {error_msg}")
    
    def _create_question_prompt(self, text: str, num_questions: int, difficulty: str) -> str:
        """Kreira prompt za Gemini."""
        difficulty_instructions = {
            'easy': 'Osnovna činjenice i direktne informacije iz teksta.',
            'medium': 'Srednje teškoće, zahteva razumevanje konteksta i povezivanje ideja.',
            'hard': 'Kompleksna pitanja koja zahtevaju dubinsko razumevanje, analizu i sintezu informacija.'
        }
        
        prompt = f"""Generiši {num_questions} multiple-choice pitanja iz sledećeg teksta.

Težina pitanja: {difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}

Tekst:
{text}

VAŽNO - Uputstva za formatiranje:
- Tekst pitanja treba da bude direktan i jasan, BEZ prefiksa poput "Prema datom tekstu", "Na osnovu teksta", "Iz datog teksta" itd.
- Objašnjenje treba da bude direktno i jasno, BEZ prefiksa poput "Prema datom tekstu", "Na osnovu teksta", "Iz datog teksta" itd.
- Pitanja i objašnjenja treba da budu prirodna i tekuća, kao da su deo normalnog kviza.

Za svako pitanje generiši:
1. Tekst pitanja (jasno i precizno, BEZ prefiksa)
2. 4 opcije odgovora (A, B, C, D)
3. Tačan odgovor (A, B, C ili D)
4. Kratko objašnjenje zašto je odgovor tačan (BEZ prefiksa)

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
    
    def _clean_text(self, text: str) -> str:
        """Uklanja nepoželjne prefikse iz teksta."""
        if not text:
            return text
        
        # Lista prefiksa za uklanjanje
        prefixes_to_remove = [
            r'^Prema datom tekstu[,:]?\s*',
            r'^Na osnovu datog teksta[,:]?\s*',
            r'^Iz datog teksta[,:]?\s*',
            r'^Prema tekstu[,:]?\s*',
            r'^Na osnovu teksta[,:]?\s*',
            r'^Iz teksta[,:]?\s*',
            r'^Prema navedenom tekstu[,:]?\s*',
            r'^Na osnovu navedenog teksta[,:]?\s*',
            r'^U datom tekstu[,:]?\s*',
            r'^U tekstu[,:]?\s*',
        ]
        
        cleaned_text = text
        for prefix_pattern in prefixes_to_remove:
            cleaned_text = re.sub(prefix_pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Ukloni višestruke razmake i trim
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text
    
    def _parse_questions(self, response_text: str, chunk_id: int, title: str) -> List[Dict[str, any]]:
        """Parsira odgovor od Gemini-ja."""
        questions = []
        
        # Try to find JSON array in response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            try:
                questions_data = json.loads(json_match.group())
                
                # Handle both list and single dict
                if isinstance(questions_data, dict):
                    questions_data = [questions_data]
                
                for i, q_data in enumerate(questions_data):
                    if not isinstance(q_data, dict):
                        continue
                    
                    # Očisti tekst pitanja i objašnjenja
                    raw_question = q_data.get('question', '')
                    raw_explanation = q_data.get('explanation', '')
                    
                    cleaned_question = self._clean_text(raw_question)
                    cleaned_explanation = self._clean_text(raw_explanation)
                        
                    question = {
                        'question_id': f"{chunk_id}_{i}",
                        'chunk_id': chunk_id,
                        'chunk_title': title,
                        'question': cleaned_question,
                        'options': q_data.get('options', {}),
                        'correct_answer': q_data.get('correct_answer', ''),
                        'explanation': cleaned_explanation,
                        'difficulty': 'medium'
                    }
                    
                    # Validate question has required fields
                    if question['question'] and question['options'] and question['correct_answer']:
                        questions.append(question)
                    else:
                        logger.warning(f"Pitanje {i} u chunk-u {chunk_id} nema sve potrebne podatke")
                        
            except json.JSONDecodeError as e:
                logger.error(f"Greška pri parsiranju JSON-a: {e}")
                logger.debug(f"Response text (prvih 500 karaktera): {response_text[:500]}")
                
                # Try to extract JSON from code blocks
                code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if code_block_match:
                    try:
                        questions_data = json.loads(code_block_match.group(1))
                        if isinstance(questions_data, dict):
                            questions_data = [questions_data]
                        for i, q_data in enumerate(questions_data):
                            if isinstance(q_data, dict):
                                # Očisti tekst pitanja i objašnjenja
                                raw_question = q_data.get('question', '')
                                raw_explanation = q_data.get('explanation', '')
                                
                                cleaned_question = self._clean_text(raw_question)
                                cleaned_explanation = self._clean_text(raw_explanation)
                                
                                question = {
                                    'question_id': f"{chunk_id}_{i}",
                                    'chunk_id': chunk_id,
                                    'chunk_title': title,
                                    'question': cleaned_question,
                                    'options': q_data.get('options', {}),
                                    'correct_answer': q_data.get('correct_answer', ''),
                                    'explanation': cleaned_explanation,
                                    'difficulty': 'medium'
                                }
                                if question['question'] and question['options'] and question['correct_answer']:
                                    questions.append(question)
                    except json.JSONDecodeError:
                        logger.error(f"Ne mogu da parsirujem JSON ni iz code block-a")
        else:
            logger.warning(f"Nije pronađen JSON array u odgovoru za chunk {chunk_id}")
            logger.debug(f"Response text (prvih 500 karaktera): {response_text[:500]}")
        
        return questions
    
    def generate_explanation(
        self,
        question: Dict[str, any],
        user_answer: str,
        is_correct: bool
    ) -> str:
        """Generiše objašnjenje sa Gemini."""
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
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Greška pri generisanju objašnjenja: {e}")
            return question.get('explanation', 'Nema objašnjenja.')

