"""
Export Results Module
====================
Modul za eksport rezultata kvizova u PDF i CSV format.
"""

import csv
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResultExporter:
    """
    Klasa za eksport rezultata u različite formate.
    """
    
    def __init__(self):
        """Inicijalizuje exporter."""
        self.styles = getSampleStyleSheet()
    
    def export_to_csv(
        self,
        results: List[Dict],
        quiz_title: str,
        output_path: str
    ) -> bool:
        """
        Eksportuje rezultate u CSV fajl.
        
        Args:
            results: Lista rezultata
            quiz_title: Naslov kviza
            output_path: Putanja za čuvanje CSV fajla
            
        Returns:
            True ako je uspešno
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Korisnik', 'Score', 'Ukupno Pitanja', 'Tačnost (%)',
                    'Datum', 'Vreme (sekunde)'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow({
                        'Korisnik': result.get('username', 'Nepoznato'),
                        'Score': f"{result['score']}/{result['total_questions']}",
                        'Ukupno Pitanja': result['total_questions'],
                        'Tačnost (%)': f"{result['accuracy'] * 100:.2f}",
                        'Datum': result.get('completed_at', ''),
                        'Vreme (sekunde)': result.get('time_taken', 'N/A')
                    })
            
            logger.info(f"CSV eksportovan: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Greška pri CSV eksportu: {e}")
            return False
    
    def export_to_pdf(
        self,
        results: List[Dict],
        quiz_title: str,
        output_path: str,
        include_charts: bool = False
    ) -> bool:
        """
        Eksportuje rezultate u PDF fajl.
        
        Args:
            results: Lista rezultata
            quiz_title: Naslov kviza
            output_path: Putanja za čuvanje PDF fajla
            include_charts: Da li da uključi grafikone
            
        Returns:
            True ako je uspešno
        """
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Naslov
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#8B5CF6'),
                spaceAfter=30,
                alignment=1  # Center
            )
            title = Paragraph(f"📊 Rezultati: {quiz_title}", title_style)
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Statistika
            total_results = len(results)
            avg_accuracy = sum(r['accuracy'] for r in results) / total_results if results else 0
            avg_score = sum(r['score'] for r in results) / total_results if results else 0
            
            stats_text = f"""
            <b>Ukupno rezultata:</b> {total_results}<br/>
            <b>Prosečna tačnost:</b> {avg_accuracy:.1%}<br/>
            <b>Prosečan score:</b> {avg_score:.1f}<br/>
            <b>Datum izveštaja:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            stats = Paragraph(stats_text, self.styles['Normal'])
            story.append(stats)
            story.append(Spacer(1, 0.3*inch))
            
            # Tabela rezultata
            if results:
                data = [['Korisnik', 'Score', 'Tačnost', 'Datum']]
                for result in results:
                    data.append([
                        result.get('username', 'Nepoznato'),
                        f"{result['score']}/{result['total_questions']}",
                        f"{result['accuracy']:.1%}",
                        result.get('completed_at', '')[:10] if result.get('completed_at') else ''
                    ])
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                story.append(table)
            
            doc.build(story)
            logger.info(f"PDF eksportovan: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Greška pri PDF eksportu: {e}")
            return False
    
    def export_quiz_result_to_pdf(
        self,
        result: Dict,
        quiz_title: str,
        output_path: str
    ) -> bool:
        """
        Eksportuje jedan rezultat kviza u PDF.
        
        Args:
            result: Rezultat kviza
            quiz_title: Naslov kviza
            output_path: Putanja za čuvanje
            
        Returns:
            True ako je uspešno
        """
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Naslov
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#8B5CF6'),
                spaceAfter=30,
                alignment=1
            )
            title = Paragraph(f"📊 Rezultat Kviza: {quiz_title}", title_style)
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Osnovne informacije
            info_text = f"""
            <b>Korisnik:</b> {result.get('username', 'Nepoznato')}<br/>
            <b>Score:</b> {result['score']}/{result['total_questions']}<br/>
            <b>Tačnost:</b> {result['accuracy']:.1%}<br/>
            <b>Datum:</b> {result.get('completed_at', '')}<br/>
            """
            info = Paragraph(info_text, self.styles['Normal'])
            story.append(info)
            story.append(Spacer(1, 0.3*inch))
            
            # Slabe oblasti
            if result.get('weak_areas'):
                weak_areas_title = Paragraph("<b>Najslabije Oblasti:</b>", self.styles['Heading2'])
                story.append(weak_areas_title)
                story.append(Spacer(1, 0.1*inch))
                
                weak_areas = json.loads(result['weak_areas']) if isinstance(result['weak_areas'], str) else result['weak_areas']
                for chunk_id, accuracy in weak_areas:
                    area_text = f"Segment {chunk_id}: {accuracy:.1%} tačnost"
                    story.append(Paragraph(area_text, self.styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
            
            doc.build(story)
            logger.info(f"PDF rezultat eksportovan: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Greška pri PDF eksportu rezultata: {e}")
            return False

