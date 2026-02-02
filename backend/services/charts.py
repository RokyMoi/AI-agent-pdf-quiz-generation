"""
Charts Module
=============
Modul za generisanje grafika performansi.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional
import io
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Klasa za generisanje grafika performansi.
    """
    
    def __init__(self):
        """Inicijalizuje chart generator."""
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def generate_accuracy_chart(
        self,
        results: List[Dict],
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Generiše grafikon tačnosti korisnika.
        
        Args:
            results: Lista rezultata
            output_path: Putanja za čuvanje (opciono)
            
        Returns:
            Base64 encoded image string ili None
        """
        try:
            usernames = [r.get('username', 'User') for r in results]
            accuracies = [r['accuracy'] * 100 for r in results]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(range(len(usernames)), accuracies, color='#8B5CF6', alpha=0.7)
            
            ax.set_xlabel('Korisnici', fontsize=12)
            ax.set_ylabel('Tačnost (%)', fontsize=12)
            ax.set_title('Tačnost Korisnika po Kvizu', fontsize=14, fontweight='bold')
            ax.set_xticks(range(len(usernames)))
            ax.set_xticklabels(usernames, rotation=45, ha='right')
            ax.set_ylim(0, 100)
            ax.grid(axis='y', alpha=0.3)
            
            # Dodaj vrednosti na barove
            for i, (bar, acc) in enumerate(zip(bars, accuracies)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{acc:.1f}%',
                       ha='center', va='bottom')
            
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                # Vrati kao base64
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                plt.close()
                return img_base64
        except Exception as e:
            logger.error(f"Greška pri generisanju chart-a: {e}")
            return None
    
    def generate_score_distribution(
        self,
        results: List[Dict],
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Generiše distribuciju score-ova.
        
        Args:
            results: Lista rezultata
            output_path: Putanja za čuvanje (opciono)
            
        Returns:
            Base64 encoded image string ili None
        """
        try:
            scores = [r['score'] for r in results]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(scores, bins=min(20, len(set(scores))), color='#8B5CF6', alpha=0.7, edgecolor='black')
            
            ax.set_xlabel('Score', fontsize=12)
            ax.set_ylabel('Broj Korisnika', fontsize=12)
            ax.set_title('Distribucija Score-ova', fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                plt.close()
                return img_base64
        except Exception as e:
            logger.error(f"Greška pri generisanju distribucije: {e}")
            return None
    
    def generate_progress_chart(
        self,
        user_results: List[Dict],
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Generiše grafikon napretka korisnika kroz vreme.
        
        Args:
            user_results: Lista rezultata korisnika (sortirano po datumu)
            output_path: Putanja za čuvanje (opciono)
            
        Returns:
            Base64 encoded image string ili None
        """
        try:
            dates = [r.get('completed_at', '')[:10] for r in user_results]
            accuracies = [r['accuracy'] * 100 for r in user_results]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(range(len(dates)), accuracies, marker='o', color='#8B5CF6', linewidth=2, markersize=8)
            ax.fill_between(range(len(dates)), accuracies, alpha=0.3, color='#8B5CF6')
            
            ax.set_xlabel('Kvizovi', fontsize=12)
            ax.set_ylabel('Tačnost (%)', fontsize=12)
            ax.set_title('Napredak Korisnika kroz Vreme', fontsize=14, fontweight='bold')
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, rotation=45, ha='right')
            ax.set_ylim(0, 100)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                plt.close()
                return img_base64
        except Exception as e:
            logger.error(f"Greška pri generisanju progress chart-a: {e}")
            return None

