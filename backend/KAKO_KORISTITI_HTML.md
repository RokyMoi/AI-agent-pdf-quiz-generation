# 🌐 Kako Koristiti HTML Sajt

## Brzi Start

### Korak 1: Pokrenite Gradio Aplikaciju

Otvorite terminal/command prompt i pokrenite:

```bash
python main.py
```

Aplikacija će se pokrenuti na `http://127.0.0.1:7860`

### Korak 2: Otvorite HTML Sajt

1. **Pronađite `index.html` fajl** u projektu
2. **Dvokliknite** na `index.html` ili
3. **Desni klik → Open with → Browser** (Chrome, Firefox, Edge)

### Korak 3: Uživajte!

HTML sajt će automatski učitati Gradio aplikaciju u lepom, modernom dizajnu sa:
- ✨ Belo-ljubičastim gradient pozadinom
- 📱 Full-screen iskustvom
- 🎨 AI-tematskim dizajnom

## Struktura Fajlova

```
AI Agent/
├── index.html          # Glavni HTML sajt
├── style.css           # CSS stilovi za HTML
├── gradio_theme.css    # CSS tema za Gradio (opciono)
└── main.py             # Gradio aplikacija (mora biti pokrenuta)
```

## Troubleshooting

### Problem: "Gradio aplikacija nije pokrenuta"

**Rešenje:**
1. Proverite da li je `python main.py` pokrenuto
2. Proverite da li aplikacija radi na `http://127.0.0.1:7860`
3. Otvorite link direktno u browseru da proverite

### Problem: Iframe ne učitava aplikaciju

**Rešenje:**
- Proverite da li nema CORS problema
- Pokušajte da otvorite Gradio direktno u novom tabu
- Proverite firewall/postavke browsera

### Problem: Dizajn ne izgleda dobro

**Rešenje:**
- Osvežite stranicu (F5)
- Proverite da li su `style.css` i `index.html` u istom folderu
- Proverite browser konzolu za greške (F12)

## Napredne Opcije

### Promena Porta

Ako želite da promenite port Gradio aplikacije:

1. U `main.py` promenite:
   ```python
   python main.py --server-port 8080
   ```

2. U `index.html` promenite:
   ```html
   src="http://127.0.0.1:8080"
   ```

### Custom Dizajn

Možete prilagoditi boje u `style.css`:
- `--primary-purple`: Glavna ljubičasta boja
- `--gradient-start`: Početak gradienta (bela)
- `--gradient-end`: Kraj gradienta (ljubičasta)

## Podrška

Za više informacija, pogledajte `README.md`

