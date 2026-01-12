"""
Embeddings Module
=================
Modul za vektorske embeddings za bolje filtriranje tema.
"""

from typing import List, Dict, Optional
import numpy as np
import logging

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logging.warning("sentence-transformers nije instaliran. Embeddings funkcionalnost neće raditi.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Klasa za upravljanje vektorskim embeddings-ima.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Inicijalizuje embedding manager.
        
        Args:
            model_name: Ime SentenceTransformer modela
        """
        self.model = None
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"Embedding model učitavan: {model_name}")
            except Exception as e:
                logger.error(f"Greška pri učitavanju modela: {e}")
        else:
            logger.warning("Embeddings nisu dostupni - instalirajte sentence-transformers")
    
    def generate_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Generiše embeddings za listu tekstova.
        
        Args:
            texts: Lista tekstova
            
        Returns:
            Numpy array sa embeddings-ima ili None
        """
        if not self.model:
            return None
        
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"Greška pri generisanju embeddings: {e}")
            return None
    
    def find_similar_chunks(
        self,
        query: str,
        chunks: List[Dict[str, any]],
        top_k: int = 5
    ) -> List[Dict[str, any]]:
        """
        Pronalazi najsličnije chunk-ove na osnovu query-ja.
        
        Args:
            query: Tekst za pretragu
            chunks: Lista chunk-ova
            top_k: Broj najsličnijih rezultata
            
        Returns:
            Lista najsličnijih chunk-ova
        """
        if not self.model:
            # Fallback na keyword matching
            return self._keyword_search(query, chunks, top_k)
        
        try:
            # Generiši embedding za query
            query_embedding = self.model.encode([query])[0]
            
            # Generiši embeddings za sve chunk-ove
            chunk_texts = [chunk['text'] for chunk in chunks]
            chunk_embeddings = self.model.encode(chunk_texts)
            
            # Izračunaj cosine similarity
            similarities = np.dot(chunk_embeddings, query_embedding) / (
                np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Sortiraj po sličnosti
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            similar_chunks = [chunks[i] for i in top_indices]
            return similar_chunks
        except Exception as e:
            logger.error(f"Greška pri pretrazi: {e}")
            return self._keyword_search(query, chunks, top_k)
    
    def _keyword_search(
        self,
        query: str,
        chunks: List[Dict[str, any]],
        top_k: int
    ) -> List[Dict[str, any]]:
        """Fallback keyword pretraga."""
        query_lower = query.lower()
        keywords = query_lower.split()
        
        scored_chunks = []
        for chunk in chunks:
            text_lower = chunk['text'].lower()
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scored_chunks.append((score, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:top_k]]
    
    def filter_chunks_by_topic_embeddings(
        self,
        chunks: List[Dict[str, any]],
        topic_keywords: List[str],
        threshold: float = 0.3
    ) -> List[Dict[str, any]]:
        """
        Filtrira chunk-ove po temi koristeći embeddings.
        
        Args:
            chunks: Lista chunk-ova
            topic_keywords: Lista ključnih reči
            threshold: Prag sličnosti (0-1)
            
        Returns:
            Filtrirana lista chunk-ova
        """
        if not self.model:
            # Fallback na keyword matching
            from chunking import TextChunker
            chunker = TextChunker()
            return chunker.filter_chunks_by_topic(chunks, topic_keywords)
        
        try:
            # Kombinuj sve ključne reči u jedan query
            query = ' '.join(topic_keywords)
            
            # Generiši embedding za query
            query_embedding = self.model.encode([query])[0]
            
            # Generiši embeddings za chunk-ove
            chunk_texts = [chunk['text'] for chunk in chunks]
            chunk_embeddings = self.model.encode(chunk_texts)
            
            # Izračunaj cosine similarity
            similarities = np.dot(chunk_embeddings, query_embedding) / (
                np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Filtriraj po threshold-u
            filtered_chunks = [
                chunks[i] for i, sim in enumerate(similarities) if sim >= threshold
            ]
            
            logger.info(f"Filtrirano {len(filtered_chunks)} od {len(chunks)} chunk-ova (threshold: {threshold})")
            return filtered_chunks
        except Exception as e:
            logger.error(f"Greška pri filtriranju: {e}")
            # Fallback
            from chunking import TextChunker
            chunker = TextChunker()
            return chunker.filter_chunks_by_topic(chunks, topic_keywords)

