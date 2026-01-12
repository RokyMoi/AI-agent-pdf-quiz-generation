"""
UI Module
=========
Gradio interfejs za PDF QuizMaster AI agenta.
"""

import gradio as gr
import os
from typing import Optional, Tuple
import logging

from pdf_parser import PDFParser
from chunking import TextChunker
from question_generator import QuestionGenerator
from rl_agent import RLAgent
from quiz_engine import QuizEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizUI:
    """
    Gradio UI za PDF QuizMaster aplikaciju.
    """
    
    def __init__(self):
        """Inicijalizuje UI komponente."""
        self.quiz_engine: Optional[QuizEngine] = None
        self.current_question = None
        self.current_explanation = None
        
    def upload_pdf(
        self,
        pdf_file,
        num_questions: int,
        chunk_size: int,
        topic_keywords: str
    ) -> Tuple[str, gr.update, gr.update]:
        """
        Uploaduje PDF i priprema kviz.
        
        Args:
            pdf_file: Uploaded PDF file
            num_questions: Broj pitanja
            chunk_size: Veličina chunk-a
            topic_keywords: Ključne reči za filtriranje (opciono)
            
        Returns:
            Tuple sa status porukom i update-ovanim komponentama
        """
        try:
            if pdf_file is None:
                return "Molimo uploadujte PDF fajl.", gr.update(visible=False), gr.update(visible=False)
            
            logger.info(f"Uploadovan PDF: {pdf_file.name}")
            
            # Parsiraj PDF
            parser = PDFParser()
            text = parser.extract_text(pdf_file.name)
            
            if not text or len(text.strip()) < 100:
                return "PDF je prazan ili nije mogao biti parsiran.", gr.update(visible=False), gr.update(visible=False)
            
            # Chunking
            chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=200)
            chunks = chunker.chunk_text(text, method='words')
            
            # Filtriranje po temi (ako je navedeno)
            if topic_keywords and topic_keywords.strip():
                keywords = [kw.strip() for kw in topic_keywords.split(',')]
                chunks = chunker.filter_chunks_by_topic(chunks, keywords)
            
            if not chunks:
                return "Nisu pronađeni relevantni segmenti u PDF-u.", gr.update(visible=False), gr.update(visible=False)
            
            # Inicijalizuj komponente
            try:
                question_generator = QuestionGenerator()
            except ValueError as e:
                return f"Greška sa API ključem: {str(e)}. Proverite ANTHROPIC_API_KEY.", gr.update(visible=False), gr.update(visible=False)
            
            rl_agent = RLAgent(num_chunks=len(chunks))
            
            # Kreiraj kviz engine
            self.quiz_engine = QuizEngine(
                chunks=chunks,
                question_generator=question_generator,
                rl_agent=rl_agent,
                total_questions=num_questions
            )
            
            status_msg = f"✅ PDF uspešno učitan! Pronađeno {len(chunks)} segmenata. Kviz je spreman!"
            
            return (
                status_msg,
                gr.update(visible=True),  # Quiz area
                gr.update(visible=True)   # Progress area
            )
            
        except Exception as e:
            logger.error(f"Greška pri upload-u PDF-a: {e}")
            return f"Greška: {str(e)}", gr.update(visible=False), gr.update(visible=False)
    
    def get_question(self) -> Tuple[str, str, str, str, str, str]:
        """
        Vraća sledeće pitanje.
        
        Returns:
            Tuple sa komponentama pitanja
        """
        if not self.quiz_engine:
            return (
                "Molimo prvo uploadujte PDF.",
                "", "", "", "", ""
            )
        
        if self.quiz_engine.is_complete():
            return (
                "🎉 Kviz je završen! Kliknite na 'Finalni Izveštaj' za rezultate.",
                "", "", "", "", ""
            )
        
        question = self.quiz_engine.get_next_question()
        
        if not question:
            return (
                "Nema više pitanja.",
                "", "", "", "", ""
            )
        
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
            ""  # Explanation (prazno dok korisnik ne odgovori)
        )
    
    def submit_answer(self, user_answer: str) -> Tuple[str, str, str, gr.update]:
        """
        Procesira odgovor korisnika.
        
        Args:
            user_answer: Odgovor korisnika
            
        Returns:
            Tuple sa rezultatom i objašnjenjem
        """
        if not self.quiz_engine or not self.current_question:
            return (
                "Molimo prvo uzmite pitanje.",
                "",
                "",
                gr.update(visible=False)
            )
        
        result = self.quiz_engine.submit_answer(user_answer)
        
        # Formatiraj rezultat
        if result.get('is_correct'):
            result_text = f"✅ **Tačno!** Vaš odgovor: {result['user_answer']}"
        else:
            result_text = f"❌ **Netačno.** Vaš odgovor: {result['user_answer']}, Tačan odgovor: {result['correct_answer']}"
        
        explanation = result.get('explanation', '')
        self.current_explanation = explanation
        
        # Progress info
        progress = self.quiz_engine.get_progress()
        progress_text = f"**Napredak:** {progress['questions_answered']}/{progress['total_questions']} | **Score:** {progress['score']} | **Tačnost:** {progress['accuracy']:.1%}"
        
        return (
            result_text,
            explanation,
            progress_text,
            gr.update(visible=True)  # Show next question button
        )
    
    def get_final_report(self) -> str:
        """
        Generiše finalni izveštaj.
        
        Returns:
            String sa finalnim izveštajem
        """
        if not self.quiz_engine:
            return "Kviz nije pokrenut."
        
        if not self.quiz_engine.is_complete():
            return "Kviz još nije završen. Odgovorite na sva pitanja."
        
        report = self.quiz_engine.get_final_report()
        
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
    
    def create_interface(self) -> gr.Blocks:
        """Kreira Gradio interfejs."""
        # Custom tema sa purple gradient bojama
        custom_theme = gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="purple",
            neutral_hue="slate"
        ).set(
            button_primary_background_fill="linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)",
            button_primary_background_fill_hover="linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)",
            button_primary_text_color="#FFFFFF",
            button_secondary_background_fill="rgba(255, 255, 255, 0.9)",
            button_secondary_border_color="#8B5CF6",
            button_secondary_text_color="#8B5CF6",
            background_fill_primary="#FFFFFF",
            background_fill_secondary="#FAFAFA",
            border_color_primary="#E9D5FF",
            border_color_secondary="#F3F4F6",
            shadow_spread="0px",
            shadow_drop="0 4px 20px rgba(139, 92, 246, 0.1)",
            radius_lg="15px",
            radius_md="10px",
            radius_sm="8px"
        )
        
        # Učitaj custom CSS
        custom_css = """
        <style>
        .gradio-container {
            background: linear-gradient(135deg, #FFFFFF 0%, #E9D5FF 50%, #8B5CF6 100%) !important;
        }
        button.primary {
            background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%) !important;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
        }
        button.primary:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4) !important;
        }
        </style>
        """
        
        with gr.Blocks(title="PDF QuizMaster AI", theme=custom_theme) as interface:
            # Dodaj custom CSS
            interface.css = custom_css
            
            gr.Markdown("""
            # 📚 PDF QuizMaster AI
            
            Interaktivni AI agent za učenje iz PDF dokumenata sa adaptivnim kvizom.
            
            **Kako koristiti:**
            1. Uploadujte PDF dokument
            2. Podesite broj pitanja i veličinu segmenta
            3. (Opciono) Unesite ključne reči za filtriranje tema
            4. Kliknite "Učitaj PDF i Pripremi Kviz"
            5. Odgovarajte na pitanja i učite!
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    pdf_input = gr.File(
                        label="Upload PDF Dokumenta",
                        file_types=[".pdf"]
                    )
                    
                    num_questions = gr.Slider(
                        minimum=5,
                        maximum=50,
                        value=10,
                        step=1,
                        label="Broj Pitanja"
                    )
                    
                    chunk_size = gr.Slider(
                        minimum=500,
                        maximum=3000,
                        value=1500,
                        step=100,
                        label="Veličina Segmenta (broj reči)"
                    )
                    
                    topic_keywords = gr.Textbox(
                        label="Ključne Reči za Filtriranje (opciono, odvojite zarezom)",
                        placeholder="npr. machine learning, neural networks, AI"
                    )
                    
                    upload_btn = gr.Button("Učitaj PDF i Pripremi Kviz", variant="primary")
                    
                    status_output = gr.Markdown()
                
                with gr.Column(scale=2, visible=False) as quiz_area:
                    question_display = gr.Markdown(label="Pitanje")
                    
                    with gr.Row():
                        option_a = gr.Button("A", variant="secondary")
                        option_b = gr.Button("B", variant="secondary")
                        option_c = gr.Button("C", variant="secondary")
                        option_d = gr.Button("D", variant="secondary")
                    
                    result_display = gr.Markdown(label="Rezultat")
                    explanation_display = gr.Markdown(label="Objašnjenje")
                    
                    progress_display = gr.Markdown(label="Napredak")
                    
                    with gr.Row():
                        next_question_btn = gr.Button("Sledeće Pitanje", variant="primary", visible=False)
                        final_report_btn = gr.Button("Finalni Izveštaj", variant="secondary")
                    
                    final_report_display = gr.Markdown(label="Finalni Izveštaj", visible=False)
            
            # Event handlers
            upload_btn.click(
                fn=self.upload_pdf,
                inputs=[pdf_input, num_questions, chunk_size, topic_keywords],
                outputs=[status_output, quiz_area, progress_display]
            )
            
            def handle_option_click(option: str):
                return self.submit_answer(option)
            
            option_a.click(
                fn=lambda: handle_option_click("A"),
                outputs=[result_display, explanation_display, progress_display, next_question_btn]
            )
            
            option_b.click(
                fn=lambda: handle_option_click("B"),
                outputs=[result_display, explanation_display, progress_display, next_question_btn]
            )
            
            option_c.click(
                fn=lambda: handle_option_click("C"),
                outputs=[result_display, explanation_display, progress_display, next_question_btn]
            )
            
            option_d.click(
                fn=lambda: handle_option_click("D"),
                outputs=[result_display, explanation_display, progress_display, next_question_btn]
            )
            
            def load_next_question():
                """Učitava sledeće pitanje i resetuje rezultate."""
                question_data = self.get_question()
                return (
                    question_data[0],  # question_text
                    question_data[1],  # option_a
                    question_data[2],  # option_b
                    question_data[3],  # option_c
                    question_data[4],  # option_d
                    "",  # Reset explanation
                    "",  # Reset result
                    gr.update(visible=False)  # Hide next button
                )
            
            next_question_btn.click(
                fn=load_next_question,
                outputs=[question_display, option_a, option_b, option_c, option_d, explanation_display, result_display, next_question_btn]
            )
            
            final_report_btn.click(
                fn=self.get_final_report,
                outputs=[final_report_display]
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=[final_report_display]
            )
            
            # Automatski učitaj prvo pitanje nakon upload-a
            upload_btn.click(
                fn=self.get_question,
                outputs=[question_display, option_a, option_b, option_c, option_d, explanation_display]
            )
        
        return interface


def launch_ui(share: bool = False, server_name: str = "127.0.0.1", server_port: int = 7860):
    """
    Pokreće Gradio UI.
    
    Args:
        share: Da li da kreira share link
        server_name: Server adresa
        server_port: Port servera
    """
    ui = QuizUI()
    interface = ui.create_interface()
    interface.launch(share=share, server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    launch_ui()

