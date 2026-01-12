"""
RL Agent Module
===============
Modul za Reinforcement Learning agenta koji adaptivno bira pitanja
na osnovu performansi korisnika.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RLAgent:
    """
    Reinforcement Learning agent za adaptivno učenje.
    Koristi PPO (Proximal Policy Optimization) pristup.
    """
    
    def __init__(
        self, 
        num_chunks: int,
        learning_rate: float = 0.01,
        exploration_rate: float = 0.3
    ):
        """
        Inicijalizuje RL agenta.
        
        Args:
            num_chunks: Broj chunk-ova (segmenata) u dokumentu
            learning_rate: Brzina učenja
            exploration_rate: Verovatnoća istraživanja novih chunk-ova
        """
        self.num_chunks = num_chunks
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        
        # State: performanse po chunk-ovima
        self.chunk_performance = defaultdict(lambda: {
            'correct': 0,
            'incorrect': 0,
            'total': 0,
            'accuracy': 0.5,  # Početna pretpostavka
            'difficulty_score': 0.5  # 0 = lako, 1 = teško
        })
        
        # Policy: verovatnoća izbora svakog chunk-a
        self.policy = np.ones(num_chunks) / num_chunks  # Uniformna početna distribucija
        
        # History za učenje
        self.history = []
    
    def update_state(self, chunk_id: int, is_correct: bool, difficulty: float = 0.5):
        """
        Ažurira stanje na osnovu odgovora korisnika.
        
        Args:
            chunk_id: ID chunk-a iz kog je pitanje
            is_correct: Da li je odgovor tačan
            difficulty: Težina pitanja (0-1)
        """
        perf = self.chunk_performance[chunk_id]
        
        if is_correct:
            perf['correct'] += 1
            reward = 1.0 if difficulty > 0.7 else 0.5  # Veći reward za teža pitanja
        else:
            perf['incorrect'] += 1
            reward = -1.0
        
        perf['total'] += 1
        perf['accuracy'] = perf['correct'] / perf['total'] if perf['total'] > 0 else 0.5
        
        # Ažuriraj difficulty score na osnovu performansi
        if perf['total'] >= 3:
            # Ako korisnik često greši, chunk je teži
            perf['difficulty_score'] = 1.0 - perf['accuracy']
        
        # Sačuvaj u istoriju
        self.history.append({
            'chunk_id': chunk_id,
            'is_correct': is_correct,
            'reward': reward,
            'difficulty': difficulty
        })
        
        # Ažuriraj policy
        self._update_policy(chunk_id, reward)
    
    def _update_policy(self, chunk_id: int, reward: float):
        """
        Ažurira policy na osnovu reward-a (PPO pristup).
        
        Args:
            chunk_id: ID chunk-a
            reward: Reward za akciju
        """
        # Povećaj verovatnoću izbora chunk-ova sa negativnim reward-om
        # (fokus na slabije oblasti)
        if reward < 0:
            # Povećaj verovatnoću za ovaj chunk (korisnik treba više vežbe)
            self.policy[chunk_id] += self.learning_rate * abs(reward)
        else:
            # Smanji verovatnoću (korisnik već zna)
            self.policy[chunk_id] -= self.learning_rate * reward * 0.5
        
        # Normalizuj policy (sve verovatnoće moraju biti pozitivne i sumirati na 1)
        self.policy = np.maximum(self.policy, 0.01)  # Minimum verovatnoća
        self.policy = self.policy / np.sum(self.policy)
    
    def select_chunk(self, available_chunks: List[int]) -> int:
        """
        Bira sledeći chunk na osnovu policy-ja.
        
        Args:
            available_chunks: Lista dostupnih chunk ID-eva
            
        Returns:
            ID izabranog chunk-a
        """
        if not available_chunks:
            return 0
        
        # Epsilon-greedy strategija: exploration vs exploitation
        if np.random.random() < self.exploration_rate:
            # Exploration: nasumičan izbor
            return np.random.choice(available_chunks)
        else:
            # Exploitation: izaberi na osnovu policy-ja
            available_policy = np.array([self.policy[chunk_id] for chunk_id in available_chunks])
            available_policy = available_policy / np.sum(available_policy)  # Normalizuj
            
            return np.random.choice(available_chunks, p=available_policy)
    
    def select_question_difficulty(self, chunk_id: int) -> str:
        """
        Bira težinu pitanja na osnovu performansi korisnika.
        
        Args:
            chunk_id: ID chunk-a
            
        Returns:
            'easy', 'medium', ili 'hard'
        """
        perf = self.chunk_performance[chunk_id]
        accuracy = perf['accuracy']
        
        if accuracy < 0.4:
            return 'easy'  # Korisnik ima problema, počni sa lakim
        elif accuracy < 0.7:
            return 'medium'
        else:
            return 'hard'  # Korisnik dobro zna, daj teža pitanja
    
    def get_weak_areas(self, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Vraća top K najslabijih oblasti (chunk-ova).
        
        Args:
            top_k: Broj oblasti za vraćanje
            
        Returns:
            Lista tuple-a (chunk_id, accuracy)
        """
        chunk_accuracies = [
            (chunk_id, perf['accuracy'])
            for chunk_id, perf in self.chunk_performance.items()
            if perf['total'] > 0
        ]
        
        # Sortiraj po accuracy (najniža = najslabija)
        chunk_accuracies.sort(key=lambda x: x[1])
        
        return chunk_accuracies[:top_k]
    
    def get_statistics(self) -> Dict:
        """
        Vraća statistiku performansi agenta.
        
        Returns:
            Rečnik sa statistikama
        """
        total_questions = sum(perf['total'] for perf in self.chunk_performance.values())
        total_correct = sum(perf['correct'] for perf in self.chunk_performance.values())
        
        overall_accuracy = total_correct / total_questions if total_questions > 0 else 0.0
        
        return {
            'total_questions': total_questions,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'chunks_covered': len(self.chunk_performance),
            'weak_areas': self.get_weak_areas(5)
        }

