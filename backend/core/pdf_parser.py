"""
PDF Parser Module
=================
Modul za ekstrakciju teksta iz PDF dokumenata.
Podržava velike PDF-ove (stotine ili hiljade stranica).
"""

import pdfplumber
import PyPDF2
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """
    Klasa za parsiranje PDF dokumenata.
    Koristi pdfplumber kao primarni parser, sa fallback na PyPDF2.
    """
    
    def __init__(self, use_pdfplumber: bool = True, progress_callback=None):
        """
        Inicijalizuje PDF parser.
        
        Args:
            use_pdfplumber: Ako je True, koristi pdfplumber, inače PyPDF2
            progress_callback: Funkcija koja se poziva sa (current_page, total_pages, status)
        """
        self.use_pdfplumber = use_pdfplumber
        self.progress_callback = progress_callback
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Ekstraktuje sav tekst iz PDF-a.
        
        Args:
            pdf_path: Putanja do PDF fajla
            
        Returns:
            String sa svim tekstom iz PDF-a
        """
        try:
            if self.use_pdfplumber:
                return self._extract_with_pdfplumber(pdf_path)
            else:
                return self._extract_with_pypdf2(pdf_path)
        except Exception as e:
            logger.error(f"Greška pri parsiranju PDF-a: {e}")
            # Fallback na alternativni parser
            if self.use_pdfplumber:
                logger.info("Pokušavam sa PyPDF2...")
                return self._extract_with_pypdf2(pdf_path)
            else:
                logger.info("Pokušavam sa pdfplumber...")
                return self._extract_with_pdfplumber(pdf_path)
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Ekstraktuje tekst koristeći pdfplumber."""
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"Parsiranje PDF-a sa {total_pages} stranica...")
            
            if self.progress_callback:
                self.progress_callback(0, total_pages, f"Počinjem parsiranje PDF-a sa {total_pages} stranica...")
            
            for i, page in enumerate(pdf.pages):
                current_page = i + 1
                progress_pct = int((current_page / total_pages) * 100)
                
                # Callback za svaku stranicu
                if self.progress_callback:
                    self.progress_callback(current_page, total_pages, f"Parsiranje stranice {current_page}/{total_pages} ({progress_pct}%)...")
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Obrađeno {i + 1}/{total_pages} stranica...")
                
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            if self.progress_callback:
                self.progress_callback(total_pages, total_pages, f"Završeno parsiranje svih {total_pages} stranica!")
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"Uspešno ekstraktovan tekst ({len(full_text)} karaktera)")
        return full_text
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """Ekstraktuje tekst koristeći PyPDF2."""
        text_parts = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"Parsiranje PDF-a sa {total_pages} stranica...")
            
            if self.progress_callback:
                self.progress_callback(0, total_pages, f"Počinjem parsiranje PDF-a sa {total_pages} stranica (PyPDF2)...")
            
            for i, page in enumerate(pdf_reader.pages):
                current_page = i + 1
                progress_pct = int((current_page / total_pages) * 100)
                
                # Callback za svaku stranicu
                if self.progress_callback:
                    self.progress_callback(current_page, total_pages, f"Parsiranje stranice {current_page}/{total_pages} ({progress_pct}%)...")
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Obrađeno {i + 1}/{total_pages} stranica...")
                
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            if self.progress_callback:
                self.progress_callback(total_pages, total_pages, f"Završeno parsiranje svih {total_pages} stranica!")
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"Uspešno ekstraktovan tekst ({len(full_text)} karaktera)")
        return full_text
    
    def extract_text_by_pages(self, pdf_path: str, start_page: int = 0, end_page: Optional[int] = None) -> str:
        """
        Ekstraktuje tekst iz određenih stranica PDF-a.
        
        Args:
            pdf_path: Putanja do PDF fajla
            start_page: Početna stranica (0-indexed)
            end_page: Završna stranica (None = do kraja)
            
        Returns:
            String sa tekstom iz odabranih stranica
        """
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            end_page = end_page if end_page is not None else total_pages
            
            for i in range(start_page, min(end_page, total_pages)):
                text = pdf.pages[i].extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)

