"""
REST API Server for PDF QuizMaster AI
======================================
REST API wrapper za frontend aplikaciju.
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import tempfile
from dotenv import load_dotenv
import logging
import json as json_lib
import threading
import queue
import time

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from pdf_parser import PDFParser
from chunking import TextChunker
from google_gemini_generator import GeminiQuestionGenerator
from rl_agent import RLAgent
from quiz_engine import QuizEngine
from database import Database
from auth_api import AuthAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to load .env, but don't fail if it doesn't exist or is corrupted
try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Ne mogu da učitam .env fajl: {e}. Koristiću default API key.")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

db = Database()
auth_api = AuthAPI()

# Check API key on startup
def check_api_key():
    """Proverava da li je GOOGLE_API_KEY postavljen i validan."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        # Use default key
        default_key = "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
        logger.info(f"GOOGLE_API_KEY nije postavljen, koristim default key...")
        os.environ['GOOGLE_API_KEY'] = default_key
        api_key = default_key
    
    try:
        # Test API key by creating generator
        logger.info("Testiranje API key-a sa Gemini...")
        gen = GeminiQuestionGenerator(api_key=api_key)
        logger.info("✅ GOOGLE_API_KEY je validan i spreman za upotrebu")
        return True
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"❌ GOOGLE_API_KEY greška (ValueError): {error_msg}")
        if 'API key' in error_msg.lower() or 'key' in error_msg.lower():
            print(f"\n❌ API KEY GREŠKA: {error_msg}")
            print("   Proverite da li je API key ispravan.")
        return False
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ GOOGLE_API_KEY greška: {error_msg}")
        print(f"\n❌ GREŠKA PRI PROVERI API KEY-A: {error_msg}")
        print("   Tip greške:", type(e).__name__)
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    # Ensure API key is set before checking
    if not os.getenv('GOOGLE_API_KEY'):
        default_key = "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
        os.environ['GOOGLE_API_KEY'] = default_key
        logger.info("GOOGLE_API_KEY nije postavljen u health check, koristim default key")
    
    api_key_valid = check_api_key()
    return jsonify({
        'status': 'ok',
        'api_key_valid': api_key_valid,
        'message': 'API key je validan' if api_key_valid else 'API key nije postavljen ili nije validan'
    })

@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    """Upload i parsiranje PDF-a sa real-time progress updates."""
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF fajl nije priložen'}), 400
        
        pdf_file = request.files['pdf_file']
        quiz_title = request.form.get('quiz_title', 'Untitled Quiz')
        num_questions = int(request.form.get('num_questions', 10))
        chunk_size = int(request.form.get('chunk_size', 1500))
        topic_keywords = request.form.get('topic_keywords', '')
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Create progress queue for streaming updates
        progress_queue = queue.Queue()
        
        def progress_callback(current_page, total_pages, status):
            """Callback za progres parsiranja."""
            progress_data = {
                'type': 'progress',
                'current_page': current_page,
                'total_pages': total_pages,
                'progress_pct': int((current_page / total_pages * 100)) if total_pages > 0 else 0,
                'status': status,
                'timestamp': time.time()
            }
            progress_queue.put(progress_data)
        
        def parse_pdf():
            """Parsira PDF u pozadini i šalje progres."""
            try:
                # Parse PDF with progress callback
                parser = PDFParser(progress_callback=progress_callback)
                text = parser.extract_text(tmp_path)
                
                if not text or len(text.strip()) < 100:
                    progress_queue.put({
                        'type': 'error',
                        'message': 'PDF je prazan ili nije mogao biti parsiran'
                    })
                    return
                
                # Chunking progress callback
                def chunking_progress_callback(current_chunk, total_chunks, status):
                    """Callback za progres chunking-a."""
                    progress_data = {
                        'type': 'progress',
                        'stage': 'chunking',
                        'current_chunk': current_chunk,
                        'total_chunks': total_chunks,
                        'progress_pct': int((current_chunk / total_chunks * 100)) if total_chunks > 0 else 0,
                        'status': status,
                        'timestamp': time.time()
                    }
                    progress_queue.put(progress_data)
                
                chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=200, progress_callback=chunking_progress_callback)
                chunks = chunker.chunk_text(text, method='words')
                
                # Filter by topic if keywords provided
                if topic_keywords:
                    keywords = [kw.strip() for kw in topic_keywords.split(',')]
                    chunks = chunker.filter_chunks_by_topic(chunks, keywords)
                
                if not chunks:
                    progress_queue.put({
                        'type': 'error',
                        'message': 'Nisu pronađeni relevantni segmenti u PDF-u'
                    })
                    return
                
                # Clean up temp file
                os.unlink(tmp_path)
                
                # Final result
                progress_queue.put({
                    'type': 'complete',
                    'success': True,
                    'chunks': chunks,
                    'num_chunks': len(chunks),
                    'message': f'PDF uspešno parsiran. Pronađeno {len(chunks)} segmenata.'
                })
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                progress_queue.put({
                    'type': 'error',
                    'message': str(e)
                })
        
        # Start parsing in background thread
        parse_thread = threading.Thread(target=parse_pdf)
        parse_thread.daemon = True
        parse_thread.start()
        
        # Stream progress updates
        def generate():
            while True:
                try:
                    # Get progress update (with timeout)
                    item = progress_queue.get(timeout=1)
                    
                    if item['type'] == 'complete':
                        yield f"data: {json_lib.dumps(item)}\n\n"
                        break
                    elif item['type'] == 'error':
                        yield f"data: {json_lib.dumps(item)}\n\n"
                        break
                    else:
                        yield f"data: {json_lib.dumps(item)}\n\n"
                        
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json_lib.dumps({'type': 'heartbeat'})}\n\n"
                except Exception as e:
                    yield f"data: {json_lib.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    break
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
            
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_question_from_chunk', methods=['POST'])
def generate_question_from_chunk():
    """Generisanje jednog pitanja iz chunk-a (za PDF kviz, kao quick quiz)."""
    try:
        data = request.json
        chunk = data.get('chunk')
        question_number = data.get('question_number', 1)
        difficulty = data.get('difficulty', 'medium')
        
        if not chunk:
            return jsonify({'error': 'Chunk je obavezan'}), 400
        
        # Ensure API key is set
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            default_key = "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
            os.environ['GOOGLE_API_KEY'] = default_key
            api_key = default_key
            logger.info("Koristim default GOOGLE_API_KEY za generate_question_from_chunk")
        
        # Check API key
        try:
            question_generator = GeminiQuestionGenerator(api_key=api_key)
        except ValueError as e:
            logger.error(f"API key error in generate_question_from_chunk: {e}")
            return jsonify({'error': f'Google API key greška: {str(e)}'}), 400
        except Exception as e:
            logger.error(f"Error initializing Gemini in generate_question_from_chunk: {e}")
            return jsonify({'error': f'Greška pri inicijalizaciji Gemini: {str(e)}'}), 500
        
        # Generate single question from chunk
        logger.info(f"Generisanje pitanja {question_number} iz chunk-a {chunk.get('chunk_id', 'N/A')}...")
        
        try:
            questions = question_generator.generate_questions_from_chunk(
                chunk,
                num_questions=1,  # Generate only one question
                difficulty=difficulty
            )
            
            if not questions or len(questions) == 0:
                return jsonify({'error': 'Nije moguće generisati pitanje iz ovog chunk-a'}), 500
            
            question = questions[0]  # Take first question
            question['question_number'] = question_number
            
            logger.info(f"Uspešno generisano pitanje {question_number}")
            return jsonify(question)
            
        except ValueError as e:
            # API key or permission errors
            logger.error(f"API greška pri generisanju pitanja: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Greška pri generisanju pitanja: {e}")
            return jsonify({'error': f'Greška pri generisanju pitanja: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error in generate_question_from_chunk: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions():
    """Generisanje pitanja iz chunk-ova (legacy endpoint - koristi se za batch generisanje)."""
    try:
        data = request.json
        chunks = data.get('chunks', [])
        num_questions = data.get('num_questions', 10)
        topic_keywords = data.get('topic_keywords', '')
        
        if not chunks:
            return jsonify({'error': 'Nema chunk-ova za generisanje pitanja'}), 400
        
        # Ensure API key is set
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            default_key = "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
            os.environ['GOOGLE_API_KEY'] = default_key
            api_key = default_key
            logger.info("Koristim default GOOGLE_API_KEY za generate_questions")
        
        # Check API key
        try:
            question_generator = GeminiQuestionGenerator(api_key=api_key)
        except ValueError as e:
            logger.error(f"API key error in generate_questions: {e}")
            return jsonify({'error': f'Google API key greška: {str(e)}'}), 400
        except Exception as e:
            logger.error(f"Error initializing Gemini in generate_questions: {e}")
            return jsonify({'error': f'Greška pri inicijalizaciji Gemini: {str(e)}'}), 500
        
        # Initialize RL agent
        rl_agent = RLAgent(num_chunks=len(chunks))
        
        # Create quiz engine
        quiz_engine = QuizEngine(
            chunks=chunks,
            question_generator=question_generator,
            rl_agent=rl_agent,
            total_questions=num_questions
        )
        
        # Generate questions
        questions = []
        max_attempts = min(num_questions * 2, len(chunks) * 3)  # Limit attempts
        
        logger.info(f"Generisanje {num_questions} pitanja iz {len(chunks)} chunk-ova...")
        
        for i in range(max_attempts):
            try:
                question = quiz_engine.get_next_question()
                if question and question.get('question'):
                    questions.append(question)
                    logger.info(f"Generisano pitanje {len(questions)}/{num_questions}")
                
                if len(questions) >= num_questions:
                    break
                    
            except ValueError as e:
                # API key or permission errors - stop and return error
                logger.error(f"API greška pri generisanju pitanja: {e}")
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.warning(f"Error generating question {i+1}: {e}")
                # Continue trying other chunks
                continue
        
        if not questions:
            return jsonify({
                'error': 'Nije moguće generisati pitanja. Proverite API key, PDF sadržaj i pokušajte ponovo.'
            }), 500
        
        # Save quiz to database (if user is authenticated)
        quiz_id = None
        # TODO: Get user from token if provided
        
        return jsonify({
            'success': True,
            'quiz_id': quiz_id,
            'questions': questions,
            'num_questions': len(questions),
            'message': f'Uspešno generisano {len(questions)} pitanja.'
        })
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint (bez JWT)."""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Korisničko ime i lozinka su obavezni'}), 400
        
        # Pronađi korisnika
        user = db.get_user_by_username(username)
        if not user:
            user = db.get_user_by_email(username)
        
        if not user:
            return jsonify({'success': False, 'message': 'Neispravno korisničko ime ili lozinka'}), 401
        
        # Proveri lozinku
        if not auth_api.auth.verify_password(password, user['password_hash']):
            return jsonify({'success': False, 'message': 'Neispravno korisničko ime ili lozinka'}), 401
        
        # Vrati korisničke podatke (bez JWT tokena)
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'total_quizzes': user.get('total_quizzes', 0),
            'total_score': user.get('total_score', 0),
            'average_accuracy': user.get('average_accuracy', 0.0)
        }
        
        logger.info(f"Korisnik prijavljen: {username}")
        return jsonify({
            'success': True,
            'message': f'Dobrodošli, {user["username"]}!',
            'user': user_data
        })
            
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register endpoint (bez JWT)."""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirmPassword = data.get('confirmPassword') or data.get('confirm_password')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'Sva polja su obavezna'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Korisničko ime mora imati najmanje 3 karaktera'}), 400
        
        if '@' not in email:
            return jsonify({'success': False, 'message': 'Unesite validnu email adresu'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Lozinka mora imati najmanje 6 karaktera'}), 400
        
        if password != confirmPassword:
            return jsonify({'success': False, 'message': 'Lozinke se ne poklapaju'}), 400
        
        # Proveri da li korisnik već postoji
        if db.get_user_by_username(username):
            return jsonify({'success': False, 'message': 'Korisničko ime već postoji'}), 400
        
        if db.get_user_by_email(email):
            return jsonify({'success': False, 'message': 'Email adresa već postoji'}), 400
        
        # Kreiraj korisnika
        password_hash = auth_api.auth.hash_password(password)
        user_id = db.create_user(username, email, password_hash)
        
        if user_id:
            user = db.get_user_by_id(user_id)
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'total_quizzes': user.get('total_quizzes', 0),
                'total_score': user.get('total_score', 0),
                'average_accuracy': user.get('average_accuracy', 0.0)
            }
            logger.info(f"Korisnik registrovan: {username}")
            return jsonify({
                'success': True,
                'message': f'Uspešno ste se registrovali, {username}!',
                'user': user_data
            })
        else:
            return jsonify({'success': False, 'message': 'Greška pri kreiranju naloga'}), 500
            
    except Exception as e:
        logger.error(f"Error in register: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Vraća statistike korisnika."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID je obavezan'}), 400
        
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Neispravan user_id'}), 400
        
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        return jsonify({
            'total_quizzes': user.get('total_quizzes', 0) or 0,
            'total_score': user.get('total_score', 0) or 0,
            'average_accuracy': user.get('average_accuracy', 0.0) or 0.0
        })
    except Exception as e:
        logger.error(f"Error loading user stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_quick_question', methods=['POST'])
def generate_quick_question():
    """Generisanje jednog pitanja na osnovu teme (za brzi kviz)."""
    try:
        data = request.json
        topic = data.get('topic')
        difficulty = data.get('difficulty', 'medium')
        question_number = data.get('question_number', 1)
        
        if not topic:
            return jsonify({'error': 'Tema je obavezna'}), 400
        
        # Ensure API key is set
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            default_key = "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
            os.environ['GOOGLE_API_KEY'] = default_key
            api_key = default_key
            logger.info("Koristim default GOOGLE_API_KEY za quick quiz")
        
        # Check API key
        try:
            question_generator = GeminiQuestionGenerator(api_key=api_key)
        except ValueError as e:
            logger.error(f"API key error in generate_quick_question: {e}")
            return jsonify({'error': f'Google API key greška: {str(e)}'}), 400
        except Exception as e:
            logger.error(f"Error initializing Gemini in generate_quick_question: {e}")
            return jsonify({'error': f'Greška pri inicijalizaciji Gemini: {str(e)}'}), 500
        
        # Create a fake chunk with the topic as text
        fake_chunk = {
            'chunk_id': question_number,
            'text': f"Tema: {topic}. Generiši jedno pitanje o ovoj temi.",
            'title': topic
        }
        
        # Generate one question
        questions = question_generator.generate_questions_from_chunk(
            fake_chunk,
            num_questions=1,
            difficulty=difficulty
        )
        
        if not questions:
            return jsonify({'error': 'Nije moguće generisati pitanje. Pokušajte ponovo.'}), 500
        
        return jsonify(questions[0])
        
    except ValueError as e:
        logger.error(f"API key error: {e}")
        return jsonify({'error': f'Google API key greška: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error generating quick question: {e}")
        return jsonify({'error': str(e)}), 500

def get_user_from_request():
    """Pomoćna funkcija za dobijanje korisnika iz zahteva (bez JWT)."""
    # Pokušaj da dobiješ user_id iz request body-a ili header-a
    user_id = None
    
    # Pokušaj iz JSON body-a
    if request.is_json:
        data = request.get_json(silent=True)
        if data:
            user_id = data.get('user_id')
    
    # Pokušaj iz form data
    if not user_id:
        user_id = request.form.get('user_id')
    
    # Pokušaj iz query parametara
    if not user_id:
        user_id = request.args.get('user_id')
    
    # Ako imamo user_id, vrati korisnika
    if user_id:
        try:
            user_id = int(user_id)
            user = db.get_user_by_id(user_id)
            if user:
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
        except (ValueError, TypeError):
            pass
    
    # Ako nema user_id, vrati None (opciono - dozvoljava anonimne zahteve)
    return None

@app.route('/api/my_quizzes', methods=['GET'])
def my_quizzes():
    """Vraća listu kvizova korisnika."""
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Neautorizovan pristup'}), 401
        
        user_id = user['id']  # Popravka: koristi user['id'] umesto user_id
        quizzes = db.get_user_quizzes(user_id)
        
        # Format quizzes for frontend
        formatted_quizzes = []
        for quiz in quizzes:
            formatted_quizzes.append({
                'id': quiz['id'],
                'title': quiz['title'],
                'status': quiz['status'],
                'num_questions': quiz['num_questions'],
                'created_at': quiz['created_at'],
                'updated_at': quiz['updated_at']
            })
        
        return jsonify(formatted_quizzes)
    except Exception as e:
        logger.error(f"Error loading quizzes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz_results/<int:quiz_id>', methods=['GET'])
def quiz_results(quiz_id):
    """Vraća rezultate za određeni kviz (bez JWT)."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'Korisnik nije prijavljen'}), 401
        
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Neispravan user_id'}), 400
        
        # Verify quiz ownership
        quiz = db.get_quiz(quiz_id)
        if not quiz:
            return jsonify({'error': 'Kviz nije pronađen'}), 404
        
        if quiz['user_id'] != user_id:
            return jsonify({'error': 'Nemate pristup ovom kvizu'}), 403
        
        # Get results
        results = db.get_quiz_results(quiz_id)
        
        # Calculate stats
        total_users = len(set(r['user_id'] for r in results))
        total_attempts = len(results)
        avg_score = sum(r['score'] for r in results) / total_attempts if total_attempts > 0 else 0
        avg_accuracy = sum(r['accuracy'] for r in results) / total_attempts if total_attempts > 0 else 0
        
        # Format results with user info
        formatted_results = []
        ip_analysis = {}
        
        for result in results:
            # get_quiz_results već vraća username i email iz JOIN-a
            formatted_result = {
                'id': result['id'],
                'username': result.get('username', 'N/A'),
                'email': result.get('email', 'N/A'),
                'score': result['score'],
                'total_questions': result['total_questions'],
                'accuracy': (result['accuracy'] * 100) if result.get('accuracy') else 0,  # Convert to percentage
                'completed_at': result.get('completed_at', ''),
                'ip_address': result.get('ip_address', 'N/A')
            }
            formatted_results.append(formatted_result)
            
            # IP analysis
            user_info = {'username': result.get('username', 'N/A')}
            
            # IP analysis
            ip = result.get('ip_address', '')
            if ip and ip != 'N/A':
                if ip not in ip_analysis:
                    ip_analysis[ip] = {
                        'user_count': 0,
                        'users': set(),
                        'attempt_count': 0
                    }
                ip_analysis[ip]['attempt_count'] += 1
                ip_analysis[ip]['users'].add(user_info['username'] if user_info else 'N/A')
                ip_analysis[ip]['user_count'] = len(ip_analysis[ip]['users'])
        
        # Convert sets to lists for JSON
        for ip, data in ip_analysis.items():
            data['users'] = list(data['users'])
        
        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_attempts': total_attempts,
                'avg_score': round(avg_score, 1),
                'avg_accuracy': round(avg_accuracy * 100, 1)  # Convert to percentage
            },
            'results': formatted_results,
            'ip_analysis': ip_analysis
        })
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_quiz', methods=['POST'])
def save_quiz():
    """Čuva kviz u bazu podataka (bez JWT)."""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        # Ako nema user_id, pokušaj da ga dobiješ iz user objekta
        if not user_id and data.get('user'):
            user_id = data.get('user', {}).get('id')
        
        if not user_id:
            return jsonify({'error': 'Korisnik nije prijavljen'}), 401
        
        # Proveri da li korisnik postoji
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        data = request.json
        title = data.get('title')
        questions = data.get('questions', [])
        topic = data.get('topic', '')
        difficulty = data.get('difficulty', 'medium')
        quiz_type = data.get('type', 'quick')
        
        if not title or not questions:
            return jsonify({'error': 'Naslov i pitanja su obavezni'}), 400
        
        # Save quiz
        quiz_id = db.create_quiz(
            user_id=user_id,  # Popravka: koristi user_id umesto user['id']
            title=title,
            num_questions=len(questions),
            topic_keywords=topic,
            questions_data=questions,
            status='published' if quiz_type == 'quick' else 'draft'
        )
        
        if not quiz_id:
            return jsonify({'error': 'Greška pri čuvanju kviza'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Kviz je uspešno sačuvan',
            'quiz_id': quiz_id
        })
    except Exception as e:
        logger.error(f"Error saving quiz: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Vraća kviz po ID-u."""
    try:
        quiz = db.get_quiz(quiz_id)
        if not quiz:
            return jsonify({'error': 'Kviz nije pronađen'}), 404
        
        # Format quiz for frontend
        formatted_quiz = {
            'id': quiz['id'],
            'title': quiz['title'],
            'num_questions': quiz['num_questions'],
            'topic': quiz.get('topic_keywords', ''),
            'questions': quiz.get('questions_data', [])
        }
        
        return jsonify(formatted_quiz)
    except Exception as e:
        logger.error(f"Error loading quiz: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_quiz_result', methods=['POST'])
def save_quiz_result():
    """Čuva rezultat kviza."""
    try:
        data = request.json
        quiz_id = data.get('quiz_id')
        user_id = data.get('user_id')
        score = data.get('score')
        total_questions = data.get('total_questions')
        accuracy = data.get('accuracy')
        answers_data = data.get('answers_data', [])
        time_taken = data.get('time_taken')
        ip_address = data.get('ip_address')
        
        if not quiz_id or not user_id:
            return jsonify({'error': 'Quiz ID i User ID su obavezni'}), 400
        
        logger.info(f"Saving quiz result: quiz_id={quiz_id}, user_id={user_id}, score={score}/{total_questions}, accuracy={accuracy}")
        
        # Save result
        result_id = db.save_quiz_result(
            quiz_id=quiz_id,
            user_id=user_id,
            score=score,
            total_questions=total_questions,
            accuracy=accuracy,
            answers_data=answers_data,
            time_taken=time_taken,
            ip_address=ip_address
        )
        
        if not result_id:
            logger.error(f"Failed to save quiz result for quiz {quiz_id}, user {user_id}")
            return jsonify({'error': 'Greška pri čuvanju rezultata'}), 500
        
        logger.info(f"Quiz result saved successfully: result_id={result_id}")
        return jsonify({
            'success': True,
            'message': 'Rezultat je uspešno sačuvan',
            'result_id': result_id
        })
    except Exception as e:
        logger.error(f"Error saving quiz result: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Vraća leaderboard sa najboljim korisnicima."""
    try:
        leaderboard = db.get_leaderboard(limit=100)
        logger.info(f"Leaderboard loaded: {len(leaderboard)} users")
        
        # Format leaderboard for frontend
        formatted_leaderboard = []
        for i, user in enumerate(leaderboard, 1):
            formatted_leaderboard.append({
                'rank': i,
                'username': user['username'],
                'total_quizzes': user['total_quizzes'] or 0,
                'total_score': user['total_score'] or 0,
                'average_accuracy': (user['average_accuracy'] * 100) if user['average_accuracy'] else 0,  # Convert to percentage
                'leaderboard_score': user.get('leaderboard_score', 0) or 0
            })
        
        logger.info(f"Formatted leaderboard: {len(formatted_leaderboard)} entries")
        return jsonify(formatted_leaderboard)
    except Exception as e:
        logger.error(f"Error loading leaderboard: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/public_quizzes', methods=['GET'])
def get_public_quizzes():
    """Vraća javne kvizove drugih korisnika."""
    try:
        user_id = request.args.get('user_id')
        exclude_user_id = int(user_id) if user_id else None
        
        quizzes = db.get_public_quizzes(exclude_user_id=exclude_user_id, limit=50)
        
        # Format quizzes for frontend
        formatted_quizzes = []
        for quiz in quizzes:
            formatted_quizzes.append({
                'id': quiz['id'],
                'title': quiz['title'],
                'username': quiz.get('username', 'N/A'),
                'num_questions': quiz['num_questions'],
                'created_at': quiz['created_at'],
                'topic': quiz.get('topic_keywords', '')
            })
        
        return jsonify(formatted_quizzes)
    except Exception as e:
        logger.error(f"Error loading public quizzes: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Set default API key if not in .env
    if not os.getenv('GOOGLE_API_KEY'):
        os.environ['GOOGLE_API_KEY'] = "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
        print("ℹ️  Koristim default GOOGLE_API_KEY (nije postavljen u .env)")
    
    # Check API key on startup
    api_key_valid = check_api_key()
    if not api_key_valid:
        print("⚠️  UPOZORENJE: GOOGLE_API_KEY nije validan!")
        print("   Proverite API key u .env fajlu.")
    else:
        print("✅ GOOGLE_API_KEY je validan i spreman za upotrebu")
    
    print("\n🚀 Pokretanje REST API servera...")
    print("   API dostupan na: http://127.0.0.1:5000")
    print("   Health check: http://127.0.0.1:5000/api/health\n")
    app.run(host='127.0.0.1', port=5000, debug=True)

