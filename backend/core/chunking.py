"""
Chunking Module
===============
Modul za segmentaciju teksta na manje delove za obradu.
Podržava chunking po broju reči ili po poglavljima.
"""

import re
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunker:
    """
    Klasa za podelu teksta na segmente (chunk-ove).
    """
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200, progress_callback=None):
        """
        Inicijalizuje chunker.
        
        Args:
            chunk_size: Broj reči po chunk-u (default: 1500)
            chunk_overlap: Broj reči preklapanja između chunk-ova (default: 200)
            progress_callback: Funkcija koja se poziva sa (current_chunk, total_chunks, status)
        """
        if chunk_overlap >= chunk_size:
            logger.warning(f"chunk_overlap ({chunk_overlap}) >= chunk_size ({chunk_size}). Ograničavam overlap na {chunk_size - 1}")
            chunk_overlap = max(1, chunk_size - 1)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.progress_callback = progress_callback
    
    def chunk_by_words(self, text: str) -> List[Dict[str, any]]:
        """
        Deli tekst na segmente po broju reči.
        
        Args:
            text: Tekst za chunking
            
        Returns:
            Lista rečnika sa segmentima i metapodacima
        """
        words = text.split()
        chunks = []
        
        if self.progress_callback:
            self.progress_callback(0, 0, f"Počinjem segmentaciju teksta ({len(words)} reči)...")
        
        if len(words) <= self.chunk_size:
            if self.progress_callback:
                self.progress_callback(1, 1, f"Tekst je mali, kreiran 1 segment ({len(words)} reči)")
            return [{
                'text': text,
                'chunk_id': 0,
                'word_count': len(words),
                'start_word': 0,
                'end_word': len(words)
            }]
        
        # Procijeni ukupan broj chunk-ova
        estimated_chunks = (len(words) + self.chunk_size - self.chunk_overlap - 1) // (self.chunk_size - self.chunk_overlap)
        
        start_idx = 0
        chunk_id = 0
        
        while start_idx < len(words):
            end_idx = min(start_idx + self.chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'text': chunk_text,
                'chunk_id': chunk_id,
                'word_count': len(chunk_words),
                'start_word': start_idx,
                'end_word': end_idx
            })
            
            # Progress callback
            if self.progress_callback:
                progress_pct = int((chunk_id + 1) / estimated_chunks * 100) if estimated_chunks > 0 else 0
                self.progress_callback(
                    chunk_id + 1, 
                    estimated_chunks,
                    f"Kreiran segment {chunk_id + 1}/{estimated_chunks} ({progress_pct}%) - {len(chunk_words)} reči"
                )
            
            # Preklapanje za sledeći chunk - osiguraj da start_idx uvek napreduje
            new_start_idx = end_idx - self.chunk_overlap
            if new_start_idx <= start_idx:
                # Ako preklapanje ne napreduje, pomeri se bar za 1 da izbegnemo beskonačnu petlju
                start_idx = end_idx
            else:
                start_idx = new_start_idx
            
            chunk_id += 1
            
            # Sigurnosna provera: ako smo prešli preko 10x estimated_chunks, zaustavi se
            if chunk_id > estimated_chunks * 10:
                logger.warning(f"Zaustavljanje segmentacije: prekoračen limit ({chunk_id} > {estimated_chunks * 10}). Možda postoji bug u logici.")
                break
        
        if self.progress_callback:
            self.progress_callback(len(chunks), len(chunks), f"✓ Završena segmentacija: {len(chunks)} segmenata od {len(words)} reči")
        
        logger.info(f"Kreirano {len(chunks)} chunk-ova od teksta sa {len(words)} reči")
        return chunks
    
    def chunk_by_chapters(self, text: str) -> List[Dict[str, any]]:
        """
        Deli tekst na segmente po poglavljima (pretpostavlja strukturu sa naslovima).
        
        Args:
            text: Tekst za chunking
            
        Returns:
            Lista rečnika sa segmentima po poglavljima
        """
        # Pokušaj da detektuje poglavlja po različitim pattern-ima
        chapter_patterns = [
            r'^Chapter\s+\d+[:\s]',  # "Chapter 1:"
            r'^CHAPTER\s+\d+[:\s]',  # "CHAPTER 1:"
            r'^\d+\.\s+[A-Z]',       # "1. NASLOV"
            r'^[A-Z][A-Z\s]{10,}',   # Velika slova (naslov)
        ]
        
        lines = text.split('\n')
        chapters = []
        current_chapter = []
        current_title = "Uvod"
        chapter_id = 0
        
        for line in lines:
            is_chapter_start = False
            for pattern in chapter_patterns:
                if re.match(pattern, line.strip()):
                    # Sačuvaj prethodno poglavlje
                    if current_chapter:
                        chapters.append({
                            'text': '\n'.join(current_chapter),
                            'chunk_id': chapter_id,
                            'title': current_title,
                            'word_count': len(' '.join(current_chapter).split())
                        })
                        chapter_id += 1
                    
                    # Počni novo poglavlje
                    current_title = line.strip()
                    current_chapter = [line]
                    is_chapter_start = True
                    break
            
            if not is_chapter_start:
                current_chapter.append(line)
        
        # Dodaj poslednje poglavlje
        if current_chapter:
            chapters.append({
                'text': '\n'.join(current_chapter),
                'chunk_id': chapter_id,
                'title': current_title,
                'word_count': len(' '.join(current_chapter).split())
            })
        
        # Ako nema poglavlja, podeli po rečima
        if len(chapters) <= 1:
            logger.info("Nisu pronađena poglavlja, koristim chunking po rečima")
            return self.chunk_by_words(text)
        
        logger.info(f"Pronađeno {len(chapters)} poglavlja")
        return chapters
    
    def chunk_text(self, text: str, method: str = 'words') -> List[Dict[str, any]]:
        """
        Glavna metoda za chunking teksta.
        
        Args:
            text: Tekst za chunking
            method: Metoda chunking-a ('words' ili 'chapters')
            
        Returns:
            Lista rečnika sa segmentima
        """
        if method == 'chapters':
            return self.chunk_by_chapters(text)
        else:
            return self.chunk_by_words(text)
    
    def filter_chunks_by_topic(self, chunks: List[Dict[str, any]], keywords: List[str]) -> List[Dict[str, any]]:
        """
        Filtrira chunk-ove koji sadrže određene ključne reči.
        
        Args:
            chunks: Lista chunk-ova
            keywords: Lista ključnih reči za filtriranje
            
        Returns:
            Filtrirana lista chunk-ova
        """
        if self.progress_callback:
            self.progress_callback(0, len(chunks), f"Filtriranje {len(chunks)} segmenata po temi: {', '.join(keywords)}...")
        
        filtered = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for i, chunk in enumerate(chunks):
            text_lower = chunk['text'].lower()
            if any(keyword in text_lower for keyword in keywords_lower):
                filtered.append(chunk)
            
            # Progress callback
            if self.progress_callback and (i + 1) % 10 == 0 or i == len(chunks) - 1:
                progress_pct = int((i + 1) / len(chunks) * 100)
                self.progress_callback(
                    i + 1,
                    len(chunks),
                    f"Proveren segment {i + 1}/{len(chunks)} ({progress_pct}%) - Pronađeno {len(filtered)} relevantnih"
                )
        
        if self.progress_callback:
            self.progress_callback(len(chunks), len(chunks), f"✓ Filtriranje završeno: {len(filtered)} od {len(chunks)} segmenata")
        
        logger.info(f"Filtrirano {len(filtered)} od {len(chunks)} chunk-ova")
        return filtered

