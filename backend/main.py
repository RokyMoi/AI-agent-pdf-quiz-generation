"""
PDF QuizMaster AI - Main Application
=====================================
Glavni aplikacioni fajl za pokretanje PDF QuizMaster AI agenta.
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Import sa auth ili bez auth
try:
    from ui_with_auth import launch_ui
    HAS_AUTH = True
except ImportError:
    from ui import launch_ui
    HAS_AUTH = False

# Učitaj environment varijable iz .env fajla (ako postoji i nije korumpiran)
try:
    load_dotenv()
except Exception as e:
    print(f"⚠️  Upozorenje: Ne mogu da učitam .env fajl: {e}")
    print("   Koristiću default API key iz koda.\n")

def main():
    """Glavna funkcija za pokretanje aplikacije."""
    parser = argparse.ArgumentParser(
        description="PDF QuizMaster AI - Interaktivni AI agent za učenje iz PDF dokumenata"
    )
    
    parser.add_argument(
        '--share',
        action='store_true',
        help='Kreira share link za Gradio (za pristup preko interneta)'
    )
    
    parser.add_argument(
        '--server-name',
        type=str,
        default='127.0.0.1',
        help='Server adresa (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--server-port',
        type=int,
        default=7860,
        help='Server port (default: 7860)'
    )
    
    args = parser.parse_args()
    
    # Proveri da li je API ključ postavljen
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("⚠️  UPOZORENJE: GOOGLE_API_KEY nije postavljen u .env fajlu!")
        print("   Koristim default API key: AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc")
        os.environ['GOOGLE_API_KEY'] = "AIzaSyCHtud1DZpBs9vPjgoXEmxLZBHDtZytuSc"
    else:
        print(f"✅ GOOGLE_API_KEY je postavljen (prvih 10 karaktera: {api_key[:10]}...)")
    
    print("🚀 Pokretanje PDF QuizMaster AI...")
    print(f"   Server: http://{args.server_name}:{args.server_port}")
    if args.share:
        print("   Share link će biti kreiran nakon pokretanja.")
    print()
    
    try:
        launch_ui(
            share=args.share,
            server_name=args.server_name,
            server_port=args.server_port
        )
    except KeyboardInterrupt:
        print("\n\n👋 Aplikacija je zaustavljena.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Greška pri pokretanju aplikacije: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

