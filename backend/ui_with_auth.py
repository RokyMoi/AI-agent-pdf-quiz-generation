"""
UI Module with Authentication
==============================
Gradio interfejs sa login/registracijom, leaderboard, my quizzes, itd.
"""

import gradio as gr
import os
from typing import Optional, Tuple, Dict, List
import logging
import json
from datetime import datetime

from pdf_parser import PDFParser
from chunking import TextChunker
from google_gemini_generator import GeminiQuestionGenerator
from rl_agent import RLAgent
from quiz_engine import QuizEngine
from database import Database
from auth_api import AuthAPI
try:
    from export_results import ResultExporter
    from charts import ChartGenerator
    from embeddings import EmbeddingManager
    HAS_EXTRAS = True
except ImportError:
    HAS_EXTRAS = False
    ResultExporter = None
    ChartGenerator = None
    EmbeddingManager = None
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizUIWithAuth:
    """
    Gradio UI sa autentifikacijom i dodatnim funkcionalnostima.
    """
    
    def __init__(self):
        """Inicijalizuje UI komponente."""
        self.quiz_engine: Optional[QuizEngine] = None
        self.current_question = None
        self.current_explanation = None
        self.current_user: Optional[Dict] = None
        self.current_token: Optional[str] = None
        self.current_quiz_id: Optional[int] = None
        self.preview_mode = False
        
        self.db = Database()
        self.auth_api = AuthAPI()
        if HAS_EXTRAS:
            self.exporter = ResultExporter()
            self.chart_generator = ChartGenerator()
            self.embedding_manager = EmbeddingManager()
        else:
            self.exporter = None
            self.chart_generator = None
            self.embedding_manager = None
    
    # Authentication methods
    def handle_register(
        self,
        username: str,
        email: str,
        password: str,
        confirm_password: str
    ) -> Tuple[str, gr.update, gr.update, gr.update]:
        """Registruje novog korisnika."""
        success, message, token = self.auth_api.register(username, email, password, confirm_password)
        
        if success:
            self.current_token = token
            self.current_user = self.auth_api.verify_user(token)
            return (
                f"✅ {message}",
                gr.update(visible=False),  # Hide login/register
                gr.update(visible=True),   # Show main app
                gr.update(value=self.current_user['username'])
            )
        else:
            return (
                f"❌ {message}",
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update()
            )
    
    def handle_login(
        self,
        username: str,
        password: str
    ) -> Tuple[str, gr.update, gr.update, gr.update]:
        """Prijavljuje korisnika."""
        success, message, token, user_data = self.auth_api.login(username, password)
        
        if success:
            self.current_token = token
            self.current_user = user_data
            return (
                f"✅ {message}",
                gr.update(visible=False),  # Hide login/register
                gr.update(visible=True),   # Show main app
                gr.update(value=self.current_user['username'])
            )
        else:
            return (
                f"❌ {message}",
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update()
            )
    
    def handle_logout(self) -> Tuple[gr.update, gr.update, gr.update]:
        """Odjavljuje korisnika."""
        self.current_user = None
        self.current_token = None
        self.quiz_engine = None
        self.current_quiz_id = None
        return (
            gr.update(visible=True),   # Show login/register
            gr.update(visible=False), # Hide main app
            gr.update(value="")
        )
    
    # Quiz creation with save/preview
    def upload_pdf(
        self,
        pdf_file,
        quiz_title: str,
        num_questions: int,
        chunk_size: int,
        topic_keywords: str
    ) -> Tuple[str, gr.update, gr.update, gr.update, gr.update]:
        """Uploaduje PDF i priprema kviz sa opcijom za čuvanje."""
        try:
            if pdf_file is None:
                return "Molimo uploadujte PDF fajl.", gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update()
            
            if not quiz_title or not quiz_title.strip():
                return "Unesite naslov kviza.", gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update()
            
            logger.info(f"Uploadovan PDF: {pdf_file.name}")
            
            # Parsiraj PDF
            parser = PDFParser()
            text = parser.extract_text(pdf_file.name)
            
            if not text or len(text.strip()) < 100:
                return "PDF je prazan ili nije mogao biti parsiran.", gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update()
            
            # Chunking
            chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=200)
            chunks = chunker.chunk_text(text, method='words')
            
            # Filtriranje po temi - koristi embeddings ako su dostupni
            if topic_keywords and topic_keywords.strip():
                keywords = [kw.strip() for kw in topic_keywords.split(',')]
                # Pokušaj sa embeddings, fallback na keyword matching
                if self.embedding_manager and self.embedding_manager.model:
                    chunks = self.embedding_manager.filter_chunks_by_topic_embeddings(
                        chunks, keywords, threshold=0.3
                    )
                else:
                    chunks = chunker.filter_chunks_by_topic(chunks, keywords)
            
            if not chunks:
                return "Nisu pronađeni relevantni segmenti u PDF-u.", gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update()
            
            # Inicijalizuj komponente - koristi samo Google Gemini
            try:
                question_generator = GeminiQuestionGenerator()
                logger.info("Koristi se Google Gemini za generisanje pitanja")
            except ValueError as e:
                return f"Greška sa Google API ključem: {str(e)}. Proverite GOOGLE_API_KEY u .env fajlu.", gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update()
            except Exception as e:
                return f"Greška pri inicijalizaciji Gemini: {str(e)}", gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update()
            
            rl_agent = RLAgent(num_chunks=len(chunks))
            
            # Kreiraj kviz engine
            self.quiz_engine = QuizEngine(
                chunks=chunks,
                question_generator=question_generator,
                rl_agent=rl_agent,
                total_questions=num_questions
            )
            
            # Sačuvaj kao draft ako je korisnik prijavljen
            if self.current_user:
                quiz_id = self.db.create_quiz(
                    user_id=self.current_user['id'],
                    title=quiz_title,
                    pdf_filename=os.path.basename(pdf_file.name),
                    pdf_path=pdf_file.name,
                    num_questions=num_questions,
                    chunk_size=chunk_size,
                    topic_keywords=topic_keywords if topic_keywords else None,
                    chunks_data=chunks,
                    status='draft'
                )
                self.current_quiz_id = quiz_id
            
            status_msg = f"✅ PDF uspešno učitan! Pronađeno {len(chunks)} segmenata. Kviz je spreman!"
            
            return (
                status_msg,
                gr.update(visible=True),  # Quiz area
                gr.update(visible=True),  # Progress area
                gr.update(visible=True),  # Save/Preview buttons
                gr.update(value=quiz_title if self.current_user else "")
            )
            
        except Exception as e:
            logger.error(f"Greška pri upload-u PDF-a: {e}")
            return f"Greška: {str(e)}", gr.update(visible=False), gr.update(visible=False), gr.update(), gr.update()
    
    def save_quiz(self, quiz_title: str) -> str:
        """Čuva kviz u bazu."""
        if not self.current_user:
            return "❌ Morate biti prijavljeni da biste sačuvali kviz."
        
        if not self.quiz_engine:
            return "❌ Nema kviza za čuvanje."
        
        if not quiz_title or not quiz_title.strip():
            return "❌ Unesite naslov kviza."
        
        # Generiši sva pitanja ako već nisu generisana
        questions = []
        for chunk_id in self.quiz_engine.questions_cache:
            questions.extend(self.quiz_engine.questions_cache[chunk_id])
        
        # Ažuriraj ili kreiraj kviz
        if self.current_quiz_id:
            self.db.update_quiz_questions(self.current_quiz_id, questions)
            self.db.update_quiz_status(self.current_quiz_id, 'published')
            return f"✅ Kviz '{quiz_title}' je sačuvan i objavljen!"
        else:
            # Kreiraj novi kviz
            quiz_id = self.db.create_quiz(
                user_id=self.current_user['id'],
                title=quiz_title,
                num_questions=self.quiz_engine.total_questions,
                chunks_data=self.quiz_engine.chunks,
                questions_data=questions,
                status='published'
            )
            if quiz_id:
                self.current_quiz_id = quiz_id
                return f"✅ Kviz '{quiz_title}' je sačuvan i objavljen!"
            else:
                return "❌ Greška pri čuvanju kviza."
    
    def preview_quiz(self) -> Tuple[str, gr.update]:
        """Prikazuje preview kviza."""
        if not self.quiz_engine:
            return "❌ Nema kviza za preview.", gr.update(visible=False)
        
        # Generiši prvo pitanje za preview
        question = self.quiz_engine.get_next_question()
        if not question:
            return "❌ Nema pitanja za prikaz.", gr.update(visible=False)
        
        self.preview_mode = True
        preview_text = f"""
## 📋 Preview Kviza

**Broj pitanja:** {self.quiz_engine.total_questions}
**Broj segmenata:** {len(self.quiz_engine.chunks)}

### Prvo Pitanje:

**{question['question']}**

**Opcije:**
- A: {question['options'].get('A', '')}
- B: {question['options'].get('B', '')}
- C: {question['options'].get('C', '')}
- D: {question['options'].get('D', '')}

**Tačan odgovor:** {question['correct_answer']}
"""
        
        return preview_text, gr.update(visible=True)
    
    # Existing quiz methods (get_question, submit_answer, etc.)
    def get_question(self) -> Tuple[str, str, str, str, str, str]:
        """Vraća sledeće pitanje."""
        if not self.quiz_engine:
            return "Molimo prvo uploadujte PDF.", "", "", "", "", ""
        
        if self.quiz_engine.is_complete():
            return "🎉 Kviz je završen! Kliknite na 'Finalni Izveštaj' za rezultate.", "", "", "", "", ""
        
        question = self.quiz_engine.get_next_question()
        
        if not question:
            return "Nema više pitanja.", "", "", "", "", ""
        
        self.current_question = question
        
        question_text = f"**Pitanje {question['question_index'] + 1} od {question['total_questions']}:**\n\n{question['question']}"
        option_a = question['options'].get('A', '')
        option_b = question['options'].get('B', '')
        option_c = question['options'].get('C', '')
        option_d = question['options'].get('D', '')
        
        return (
            question_text,
            option_a,
            option_b,
            option_c,
            option_d,
            ""
        )
    
    def submit_answer(self, user_answer: str) -> Tuple[str, str, str, gr.update]:
        """Procesira odgovor korisnika."""
        if not self.quiz_engine or not self.current_question:
            return "Molimo prvo uzmite pitanje.", "", "", gr.update(visible=False)
        
        result = self.quiz_engine.submit_answer(user_answer)
        
        if result.get('is_correct'):
            result_text = f"✅ **Tačno!** Vaš odgovor: {result['user_answer']}"
        else:
            result_text = f"❌ **Netačno.** Vaš odgovor: {result['user_answer']}, Tačan odgovor: {result['correct_answer']}"
        
        # Generiši objašnjenje koristeći Gemini
        explanation = result.get('explanation', '')
        if not explanation and self.quiz_engine.question_generator:
            try:
                # Ako je Gemini generator, koristi njegovu metodu
                if hasattr(self.quiz_engine.question_generator, 'generate_explanation'):
                    explanation = self.quiz_engine.question_generator.generate_explanation(
                        self.current_question,
                        user_answer,
                        result.get('is_correct', False)
                    )
            except Exception as e:
                logger.error(f"Greška pri generisanju objašnjenja: {e}")
                explanation = result.get('explanation', 'Nema objašnjenja.')
        
        self.current_explanation = explanation
        
        progress = self.quiz_engine.get_progress()
        progress_text = f"**Napredak:** {progress['questions_answered']}/{progress['total_questions']} | **Score:** {progress['score']} | **Tačnost:** {progress['accuracy']:.1%}"
        
        return (
            result_text,
            explanation,
            progress_text,
            gr.update(visible=True)
        )
    
    def get_final_report(self) -> str:
        """Generiše finalni izveštaj i čuva rezultat."""
        if not self.quiz_engine:
            return "Kviz nije pokrenut."
        
        if not self.quiz_engine.is_complete():
            return "Kviz još nije završen. Odgovorite na sva pitanja."
        
        report = self.quiz_engine.get_final_report()
        
        # Sačuvaj rezultat ako je korisnik prijavljen
        if self.current_user and self.current_quiz_id:
            answers_data = [qa for qa in self.quiz_engine.questions_answered]
            self.db.save_quiz_result(
                quiz_id=self.current_quiz_id,
                user_id=self.current_user['id'],
                score=report['score'],
                total_questions=report['total_questions'],
                accuracy=report['accuracy'],
                answers_data=answers_data,
                weak_areas=report['weak_areas']
            )
        
        report_text = f"""
# 📊 Finalni Izveštaj

## Ukupni Rezultati
- **Ukupno pitanja:** {report['total_questions']}
- **Tačnih odgovora:** {report['score']}
- **Tačnost:** {report['accuracy']:.1%}

## 📈 Analiza Performansi

### Najslabije Oblasti (zahteva dodatnu vežbu):
"""
        
        for chunk_id, accuracy in report['weak_areas']:
            report_text += f"- Segment {chunk_id}: {accuracy:.1%} tačnost\n"
        
        report_text += f"\n### Pokrivenost:\n- Pokriveno segmenata: {report['chunks_covered']}\n"
        
        return report_text
    
    # Leaderboard
    def get_leaderboard(self) -> str:
        """Vraća leaderboard."""
        leaderboard = self.db.get_leaderboard(limit=50)
        
        if not leaderboard:
            return "Trenutno nema podataka za leaderboard."
        
        leaderboard_text = "# 🏆 Leaderboard\n\n"
        leaderboard_text += "| Rang | Korisnik | Ukupno Kvizova | Ukupni Score | Prosečna Tačnost |\n"
        leaderboard_text += "|------|----------|-----------------|--------------|------------------|\n"
        
        for i, user in enumerate(leaderboard, 1):
            leaderboard_text += f"| {i} | {user['username']} | {user['total_quizzes']} | {user['total_score']} | {user['average_accuracy']:.1%} |\n"
        
        return leaderboard_text
    
    # My Quizzes
    def get_my_quizzes(self) -> str:
        """Vraća kvizove trenutnog korisnika."""
        if not self.current_user:
            return "Morate biti prijavljeni da biste videli svoje kvizove."
        
        quizzes = self.db.get_user_quizzes(self.current_user['id'])
        
        if not quizzes:
            return "Nemate još uvek kreiranih kvizova."
        
        quizzes_text = f"# 📚 Moji Kvizovi ({len(quizzes)})\n\n"
        
        for quiz in quizzes:
            status_emoji = "📝" if quiz['status'] == 'draft' else "✅" if quiz['status'] == 'published' else "📦"
            quizzes_text += f"""
### {status_emoji} {quiz['title']}
- **Status:** {quiz['status']}
- **Broj pitanja:** {quiz['num_questions']}
- **Kreiran:** {quiz['created_at']}
- **ID:** {quiz['id']}

"""
        
        return quizzes_text
    
    # Other People's Quizzes
    def get_other_quizzes(self) -> str:
        """Vraća kvizove drugih korisnika."""
        user_id = self.current_user['id'] if self.current_user else None
        quizzes = self.db.get_public_quizzes(exclude_user_id=user_id, limit=50)
        
        if not quizzes:
            return "Trenutno nema javnih kvizova."
        
        quizzes_text = f"# 🌍 Kvizovi Drugih Korisnika ({len(quizzes)})\n\n"
        quizzes_text += "Kliknite na ID kviza da ga učitate.\n\n"
        
        for quiz in quizzes:
            quizzes_text += f"""
### 📖 {quiz['title']}
- **Autor:** {quiz.get('username', 'Nepoznato')}
- **Broj pitanja:** {quiz['num_questions']}
- **Kreiran:** {quiz['created_at']}
- **ID:** {quiz['id']}

"""
        
        return quizzes_text
    
    def load_quiz(self, quiz_id: int) -> str:
        """Učitava postojeći kviz iz baze."""
        if not self.current_user:
            return "❌ Morate biti prijavljeni da biste učitali kviz."
        
        quiz = self.db.get_quiz(quiz_id)
        if not quiz:
            return f"❌ Kviz sa ID {quiz_id} ne postoji."
        
        # Proveri da li korisnik ima pristup (vlasnik ili javan)
        if quiz['user_id'] != self.current_user['id'] and quiz['status'] != 'published':
            return "❌ Nemate pristup ovom kvizu."
        
        # Učitaj podatke kviza
        chunks = quiz.get('chunks_data', [])
        questions_data = quiz.get('questions_data', [])
        
        if not chunks or not questions_data:
            return "❌ Kviz nema dovoljno podataka za učitavanje."
        
        # Inicijalizuj komponente - koristi samo Google Gemini
        try:
            question_generator = GeminiQuestionGenerator()
        except ValueError as e:
            return f"❌ Greška sa Google API ključem: {str(e)}"
        
        rl_agent = RLAgent(num_chunks=len(chunks))
        
        # Kreiraj kviz engine
        self.quiz_engine = QuizEngine(
            chunks=chunks,
            question_generator=question_generator,
            rl_agent=rl_agent,
            total_questions=quiz['num_questions']
        )
        
        # Učitaj pitanja u cache
        for question in questions_data:
            chunk_id = question.get('chunk_id', 0)
            if chunk_id not in self.quiz_engine.questions_cache:
                self.quiz_engine.questions_cache[chunk_id] = []
            self.quiz_engine.questions_cache[chunk_id].append(question)
        
        self.current_quiz_id = quiz_id
        
        return f"✅ Kviz '{quiz['title']}' je uspešno učitan! Možete početi sa kvizom."
    
    # Quiz Results
    def get_quiz_results(self, quiz_id: int, include_charts: bool = True) -> Tuple[str, Optional[str]]:
        """Vraća rezultate za određeni kviz sa graficima."""
        quiz = self.db.get_quiz(quiz_id)
        if not quiz:
            return f"Kviz sa ID {quiz_id} ne postoji.", None
        
        results = self.db.get_quiz_results(quiz_id)
        
        if not results:
            return f"Kviz '{quiz['title']}' još nema rezultata.", None
        
        results_text = f"# 📊 Rezultati za: {quiz['title']}\n\n"
        results_text += f"**Ukupno rezultata:** {len(results)}\n\n"
        results_text += "| Korisnik | Score | Tačnost | Datum |\n"
        results_text += "|----------|-------|---------|-------|\n"
        
        for result in results:
            results_text += f"| {result.get('username', 'Nepoznato')} | {result['score']}/{result['total_questions']} | {result['accuracy']:.1%} | {result['completed_at']} |\n"
        
        # Generiši grafikone
        chart_html = None
        if include_charts and results and self.chart_generator:
            try:
                chart_base64 = self.chart_generator.generate_accuracy_chart(results)
                if chart_base64:
                    chart_html = f'<img src="data:image/png;base64,{chart_base64}" style="max-width:100%;" />'
            except Exception as e:
                logger.error(f"Greška pri generisanju chart-a: {e}")
        
        return results_text, chart_html
    
    def export_quiz_results(self, quiz_id: int, format_type: str = 'csv') -> str:
        """Eksportuje rezultate kviza u CSV ili PDF."""
        if not self.exporter:
            return "❌ Eksport funkcionalnost nije dostupna. Instalirajte reportlab i matplotlib."
        
        if not self.current_user:
            return "❌ Morate biti prijavljeni."
        
        quiz = self.db.get_quiz(quiz_id)
        if not quiz:
            return f"❌ Kviz sa ID {quiz_id} ne postoji."
        
        results = self.db.get_quiz_results(quiz_id)
        if not results:
            return f"❌ Kviz '{quiz['title']}' nema rezultata za eksport."
        
        # Konvertuj results u format koji exporter očekuje
        export_results = []
        for r in results:
            export_results.append({
                'username': r.get('username', 'Nepoznato'),
                'score': r['score'],
                'total_questions': r['total_questions'],
                'accuracy': r['accuracy'],
                'completed_at': r.get('completed_at', ''),
                'time_taken': r.get('time_taken')
            })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"quiz_{quiz_id}_{timestamp}"
        
        if format_type == 'csv':
            output_path = f"{filename}.csv"
            success = self.exporter.export_to_csv(export_results, quiz['title'], output_path)
        else:  # PDF
            output_path = f"{filename}.pdf"
            success = self.exporter.export_to_pdf(export_results, quiz['title'], output_path, include_charts=True)
        
        if success:
            return f"✅ Rezultati eksportovani u {output_path}"
        else:
            return f"❌ Greška pri eksportu rezultata."
    
    def create_interface(self) -> gr.Blocks:
        """Kreira kompletan Gradio interfejs."""
        custom_theme = gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="purple",
            neutral_hue="slate"
        ).set(
            button_primary_background_fill="linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)",
            button_primary_background_fill_hover="linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)",
            button_primary_text_color="#FFFFFF",
        )
        
        custom_css = """
        <style>
        .gradio-container {
            background: linear-gradient(135deg, #FFFFFF 0%, #E9D5FF 50%, #8B5CF6 100%) !important;
        }
        </style>
        """
        
        with gr.Blocks(title="PDF QuizMaster AI", theme=custom_theme) as interface:
            interface.css = custom_css
            
            # Login/Register Section
            with gr.Column(visible=True) as auth_section:
                gr.Markdown("# 🔐 Prijava / Registracija")
                
                with gr.Tabs():
                    with gr.Tab("Prijava"):
                        login_username = gr.Textbox(label="Korisničko ime ili Email")
                        login_password = gr.Textbox(label="Lozinka", type="password")
                        login_btn = gr.Button("Prijavi se", variant="primary")
                        login_status = gr.Markdown()
                    
                    with gr.Tab("Registracija"):
                        reg_username = gr.Textbox(label="Korisničko ime")
                        reg_email = gr.Textbox(label="Email")
                        reg_password = gr.Textbox(label="Lozinka", type="password")
                        reg_confirm = gr.Textbox(label="Potvrda lozinke", type="password")
                        reg_btn = gr.Button("Registruj se", variant="primary")
                        reg_status = gr.Markdown()
            
            # Main App Section
            with gr.Column(visible=False) as main_section:
                # Header with user info
                with gr.Row():
                    user_info = gr.Markdown("")
                    logout_btn = gr.Button("Odjavi se", variant="secondary", size="sm")
                
                with gr.Tabs():
                    # Create Quiz Tab
                    with gr.Tab("📝 Kreiraj Kviz"):
                        quiz_title = gr.Textbox(label="Naslov Kviza", placeholder="npr. Machine Learning Basics")
                        pdf_input = gr.File(label="Upload PDF Dokumenta", file_types=[".pdf"])
                        num_questions = gr.Slider(minimum=5, maximum=50, value=10, step=1, label="Broj Pitanja")
                        chunk_size = gr.Slider(minimum=500, maximum=3000, value=1500, step=100, label="Veličina Segmenta")
                        topic_keywords = gr.Textbox(label="Ključne Reči (opciono)", placeholder="npr. machine learning, AI")
                        
                        with gr.Row():
                            upload_btn = gr.Button("Učitaj PDF i Pripremi Kviz", variant="primary")
                            preview_btn = gr.Button("Preview Kviza", variant="secondary")
                            save_btn = gr.Button("Sačuvaj Kviz", variant="primary")
                        
                        status_output = gr.Markdown()
                        preview_output = gr.Markdown(visible=False)
                        
                        # Quiz area
                        with gr.Column(visible=False) as quiz_area:
                            question_display = gr.Markdown(label="Pitanje")
                            with gr.Row():
                                option_a = gr.Button("A", variant="secondary")
                                option_b = gr.Button("B", variant="secondary")
                                option_c = gr.Button("C", variant="secondary")
                                option_d = gr.Button("D", variant="secondary")
                            result_display = gr.Markdown(label="Rezultat")
                            explanation_display = gr.Markdown(label="Objašnjenje")
                            progress_display = gr.Markdown(label="Napredak")
                            next_question_btn = gr.Button("Sledeće Pitanje", variant="primary", visible=False)
                            final_report_btn = gr.Button("Finalni Izveštaj", variant="secondary")
                            final_report_display = gr.Markdown(label="Finalni Izveštaj")
                    
                    # My Quizzes Tab
                    with gr.Tab("📚 Moji Kvizovi"):
                        my_quizzes_btn = gr.Button("Učitaj Moje Kvizove", variant="primary")
                        my_quizzes_display = gr.Markdown()
                        load_my_quiz_id = gr.Number(label="ID Kviza za Učitavanje", value=1)
                        load_my_quiz_btn = gr.Button("Učitaj Kviz", variant="secondary")
                        load_my_quiz_status = gr.Markdown()
                    
                    # Other Quizzes Tab
                    with gr.Tab("🌍 Kvizovi Drugih"):
                        other_quizzes_btn = gr.Button("Učitaj Javne Kvizove", variant="primary")
                        other_quizzes_display = gr.Markdown()
                        load_other_quiz_id = gr.Number(label="ID Kviza za Učitavanje", value=1)
                        load_other_quiz_btn = gr.Button("Učitaj Kviz", variant="secondary")
                        load_other_quiz_status = gr.Markdown()
                    
                    # Leaderboard Tab
                    with gr.Tab("🏆 Leaderboard"):
                        leaderboard_btn = gr.Button("Učitaj Leaderboard", variant="primary")
                        leaderboard_display = gr.Markdown()
                    
                    # Quiz Results Tab
                    with gr.Tab("📊 Rezultati"):
                        quiz_id_input = gr.Number(label="ID Kviza", value=1)
                        with gr.Row():
                            results_btn = gr.Button("Prikaži Rezultate", variant="primary")
                            export_csv_btn = gr.Button("Eksportuj CSV", variant="secondary")
                            export_pdf_btn = gr.Button("Eksportuj PDF", variant="secondary")
                        results_display = gr.Markdown()
                        chart_display = gr.HTML()
                        export_status = gr.Markdown()
            
            # Event handlers
            login_btn.click(
                fn=self.handle_login,
                inputs=[login_username, login_password],
                outputs=[login_status, auth_section, main_section, user_info]
            )
            
            reg_btn.click(
                fn=self.handle_register,
                inputs=[reg_username, reg_email, reg_password, reg_confirm],
                outputs=[reg_status, auth_section, main_section, user_info]
            )
            
            logout_btn.click(
                fn=self.handle_logout,
                outputs=[auth_section, main_section, user_info]
            )
            
            upload_btn.click(
                fn=self.upload_pdf,
                inputs=[pdf_input, quiz_title, num_questions, chunk_size, topic_keywords],
                outputs=[status_output, quiz_area, progress_display, save_btn, quiz_title]
            ).then(
                fn=self.get_question,
                outputs=[question_display, option_a, option_b, option_c, option_d, explanation_display]
            )
            
            def handle_option(option: str):
                return self.submit_answer(option)
            
            option_a.click(fn=lambda: handle_option("A"), outputs=[result_display, explanation_display, progress_display, next_question_btn])
            option_b.click(fn=lambda: handle_option("B"), outputs=[result_display, explanation_display, progress_display, next_question_btn])
            option_c.click(fn=lambda: handle_option("C"), outputs=[result_display, explanation_display, progress_display, next_question_btn])
            option_d.click(fn=lambda: handle_option("D"), outputs=[result_display, explanation_display, progress_display, next_question_btn])
            
            def load_next():
                q_data = self.get_question()
                return q_data[0], q_data[1], q_data[2], q_data[3], q_data[4], "", "", gr.update(visible=False)
            
            next_question_btn.click(
                fn=load_next,
                outputs=[question_display, option_a, option_b, option_c, option_d, explanation_display, result_display, next_question_btn]
            )
            
            final_report_btn.click(
                fn=self.get_final_report,
                outputs=[final_report_display]
            )
            
            save_btn.click(
                fn=self.save_quiz,
                inputs=[quiz_title],
                outputs=[status_output]
            )
            
            preview_btn.click(
                fn=self.preview_quiz,
                outputs=[preview_output, preview_output]
            )
            
            my_quizzes_btn.click(
                fn=self.get_my_quizzes,
                outputs=[my_quizzes_display]
            )
            
            other_quizzes_btn.click(
                fn=self.get_other_quizzes,
                outputs=[other_quizzes_display]
            )
            
            leaderboard_btn.click(
                fn=self.get_leaderboard,
                outputs=[leaderboard_display]
            )
            
            results_btn.click(
                fn=self.get_quiz_results,
                inputs=[quiz_id_input],
                outputs=[results_display, chart_display]
            )
            
            export_csv_btn.click(
                fn=lambda qid: self.export_quiz_results(qid, 'csv'),
                inputs=[quiz_id_input],
                outputs=[export_status]
            )
            
            export_pdf_btn.click(
                fn=lambda qid: self.export_quiz_results(qid, 'pdf'),
                inputs=[quiz_id_input],
                outputs=[export_status]
            )
            
            load_my_quiz_btn.click(
                fn=self.load_quiz,
                inputs=[load_my_quiz_id],
                outputs=[load_my_quiz_status]
            ).then(
                fn=self.get_question,
                outputs=[question_display, option_a, option_b, option_c, option_d, explanation_display]
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[quiz_area]
            )
            
            load_other_quiz_btn.click(
                fn=self.load_quiz,
                inputs=[load_other_quiz_id],
                outputs=[load_other_quiz_status]
            ).then(
                fn=self.get_question,
                outputs=[question_display, option_a, option_b, option_c, option_d, explanation_display]
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[quiz_area]
            )
        
        return interface


def launch_ui(share: bool = False, server_name: str = "127.0.0.1", server_port: int = 7860):
    """Pokreće Gradio UI sa autentifikacijom."""
    ui = QuizUIWithAuth()
    interface = ui.create_interface()
    interface.launch(share=share, server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    launch_ui()

