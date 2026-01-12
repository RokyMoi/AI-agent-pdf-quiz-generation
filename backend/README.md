# 📚 PDF QuizMaster AI

Interaktivni, edukativni AI agent koji omogućava korisniku da uploaduje PDF dokument, generiše pitanja iz njega i vodi adaptivni kviz koristeći Reinforcement Learning (RL) principe.

## 🎯 Funkcionalnosti

### 1. **Autentifikacija i Korisnički Nalozi**
- 🔐 **Registracija i prijava** sa JWT tokenima
- 🔒 Sigurno čuvanje lozinki sa bcrypt hash-om
- 👤 Profili korisnika sa statistikama
- 🎫 Session management sa JWT autentifikacijom

### 2. **Upload PDF Dokumenta**
- Podržava velike PDF-ove (stotine ili hiljade stranica)
- Ekstraktuje tekst koristeći `pdfplumber` ili `PyPDF2`
- Automatski fallback na alternativni parser ako jedan ne radi

### 3. **Inteligentna Segmentacija**
- Podela teksta na manje segmente po poglavljima ili po broju reči
- Konfigurabilna veličina segmenta (500-3000 reči)
- Opciono filtriranje po temama (ključne reči)

### 4. **Generisanje Pitanja sa Claude AI**
- Automatsko generisanje multiple-choice pitanja iz svakog segmenta
- Pitanja sa 4 opcije (A, B, C, D)
- Različite težine (easy, medium, hard)
- Detaljna objašnjenja za svaki odgovor

### 5. **Interaktivni Kviz UI**
- Moderni Gradio web interfejs
- Prikaz pitanja i opcija
- Instant feedback nakon svakog odgovora
- Praćenje napretka u realnom vremenu

### 6. **Adaptivno Učenje sa RL**
- **Reinforcement Learning agent (PPO pristup)**
- **State**: Istorija korisnikovih odgovora po segmentima
- **Action**: Izbor sledećeg pitanja ili segmenta
- **Reward**: 
  - +1 za tačan odgovor
  - +0.5 za tačan težak odgovor
  - -1 za netačan odgovor
- **Cilj**: Maksimizovati korisnikov napredak i fokusirati pitanja na slabije oblasti

### 7. **Objašnjenja i Kontekst**
- Claude generiše detaljna objašnjenja za svaki odgovor
- Objašnjava zašto je odgovor tačan ili netačan
- Pruža dodatne činjenice i kontekst

### 8. **Čuvanje i Deljenje Kvizova**
- 💾 **Sačuvaj kviz**: Čuva kviz u bazu podataka
- 👁️ **Preview**: Pregled kviza pre objavljivanja
- 📤 **Objavi**: Objavi kviz da bude dostupan drugim korisnicima
- 📥 **Učitaj**: Učitaj postojeće kvizove iz baze

### 9. **Moji Kvizovi**
- 📚 Pregled svih svojih kvizova
- 📊 Status kvizova (draft, published, archived)
- 🔄 Učitavanje i nastavak rada na kvizovima

### 10. **Kvizovi Drugih Korisnika**
- 🌍 Pregled javnih kvizova drugih korisnika
- 🔍 Pretraga i filtriranje kvizova
- 📥 Učitavanje i rešavanje kvizova drugih korisnika

### 11. **Leaderboard**
- 🏆 Rang lista najboljih korisnika
- 📊 Sortiranje po ukupnom score-u i prosečnoj tačnosti
- 🎯 Praćenje sopstvenog ranga

### 12. **Rezultati Kvizova**
- 📊 Detaljni rezultati za svaki kviz
- 👥 Pregled rezultata svih korisnika
- 📈 Statistika performansi po kvizu

### 13. **Finalni Izveštaj**
- Statistika performansi
- Identifikacija najslabijih oblasti
- Preporuke za dodatnu vežbu
- Automatsko čuvanje rezultata u bazu

## 🚀 Instalacija

### 1. Klonirajte ili preuzmite projekat

```bash
cd "AI Agent"
```

### 2. Kreirajte virtualno okruženje (preporučeno)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalirajte dependencies

```bash
pip install -r requirements.txt
```

### 4. Postavite API ključ

1. Kopirajte `.env.example` u `.env`:
```bash
copy .env.example .env  # Windows
# ili
cp .env.example .env    # Linux/Mac
```

2. Otvorite `.env` i unesite svoj Claude API ključ:
```
ANTHROPIC_API_KEY=your_api_key_here
JWT_SECRET_KEY=your-secret-key-here-change-in-production
```

API ključ možete dobiti na: https://console.anthropic.com/

**Napomena**: `JWT_SECRET_KEY` je opciono - ako ga ne postavite, koristiće se default vrednost (ne preporučuje se za produkciju).

## 📖 Korišćenje

### Opcija 1: Direktno kroz Gradio (Terminal)

```bash
python main.py
```

Aplikacija će se pokrenuti na `http://127.0.0.1:7860`

### Opcija 2: Kroz HTML Sajt (Preporučeno)

1. **Pokrenite Gradio aplikaciju u pozadini:**
   ```bash
   python main.py
   ```

2. **Otvorite `index.html` u web browseru:**
   - Dvokliknite na `index.html` fajl
   - Ili otvorite ga direktno u browseru (Chrome, Firefox, Edge)
   - HTML sajt će automatski učitati Gradio aplikaciju u iframe-u

3. **Uživajte u modernom, full-screen iskustvu!**

HTML sajt ima:
- ✨ Moderni dizajn sa belo-ljubičastim gradient pozadinom
- 📱 Responsive dizajn (radi na svim uređajima)
- 🎨 AI-tematski dizajn sa smooth animacijama
- 📊 Informacije o funkcionalnostima
- 🚀 Full-screen iskustvo

### Opcije pokretanja

```bash
# Sa share link-om (za pristup preko interneta)
python main.py --share

# Sa custom portom
python main.py --server-port 8080

# Kombinovano
python main.py --share --server-port 8080
```

### Korak po korak u UI-u

#### Prvi put (Registracija/Prijava):
1. **Registrujte se** ili **prijavite se** sa postojećim nalogom
2. Nakon prijave, videćete glavni interfejs

#### Kreiranje Kviza:
1. **Upload PDF-a**: Kliknite na "Upload PDF Dokumenta" i izaberite fajl
2. **Unesite naslov kviza** (obavezno za čuvanje)
3. **Podesite opcije**:
   - Broj pitanja (5-50)
   - Veličina segmenta (500-3000 reči)
   - (Opciono) Ključne reči za filtriranje tema
4. **Kliknite "Učitaj PDF i Pripremi Kviz"**
5. **Preview ili Sačuvaj**: 
   - Kliknite "Preview Kviza" za pregled
   - Kliknite "Sačuvaj Kviz" da sačuvate i objavite
6. **Odgovarajte na pitanja**: Kliknite na opciju A, B, C ili D
7. **Pročitajte objašnjenje** i kliknite "Sledeće Pitanje"
8. **Pogledajte finalni izveštaj** nakon završetka kviza

#### Pregled Kvizova:
- **Moji Kvizovi**: Pregledajte sve svoje kvizove
- **Kvizovi Drugih**: Pregledajte javne kvizove drugih korisnika
- **Leaderboard**: Vidite rang listu najboljih korisnika
- **Rezultati**: Pregledajte rezultate bilo kog kviza

## 🏗️ Struktura Projekta

```
AI Agent/
├── main.py                 # Glavni aplikacioni fajl
├── ui.py                   # Gradio UI komponente (bez auth)
├── ui_with_auth.py         # Gradio UI sa autentifikacijom ⭐
├── database.py             # SQLite baza podataka
├── auth.py                 # JWT autentifikacija
├── auth_api.py             # Auth API endpoints
├── pdf_parser.py           # PDF parsiranje
├── chunking.py             # Segmentacija teksta
├── question_generator.py   # Generisanje pitanja sa Claude
├── rl_agent.py             # RL agent za adaptivno učenje
├── quiz_engine.py          # Logika kviza i koordinacija
├── requirements.txt        # Python dependencies
├── .env.example            # Primer environment varijabli
├── quizmaster.db           # SQLite baza (kreira se automatski)
└── README.md               # Dokumentacija
```

## 🔧 Konfiguracija

### Environment Varijable

- `ANTHROPIC_API_KEY`: Obavezno - Claude API ključ

### Parametri RL Agenta

U `rl_agent.py` možete podesiti:
- `learning_rate`: Brzina učenja (default: 0.01)
- `exploration_rate`: Verovatnoća istraživanja (default: 0.3)

### Parametri Chunking-a

U `chunking.py` možete podesiti:
- `chunk_size`: Broj reči po segmentu (default: 1500)
- `chunk_overlap`: Preklapanje između segmentata (default: 200)

## 🧠 Kako RL Agent Radi

1. **Inicijalizacija**: Agent počinje sa uniformnom distribucijom verovatnoća za sve segmente
2. **Praćenje performansi**: Za svaki segment prati:
   - Broj tačnih/netačnih odgovora
   - Tačnost (accuracy)
   - Težinu (difficulty score)
3. **Ažuriranje policy-ja**:
   - Povećava verovatnoću izbora segmenta gde korisnik greši (fokus na slabije oblasti)
   - Smanjuje verovatnoću za segmente gde korisnik dobro zna
4. **Epsilon-greedy strategija**: 
   - 30% vremena: nasumičan izbor (exploration)
   - 70% vremena: izbor na osnovu policy-ja (exploitation)

## 📊 Primer Output-a

### Finalni Izveštaj

```
📊 Finalni Izveštaj

## Ukupni Rezultati
- Ukupno pitanja: 10
- Tačnih odgovora: 7
- Tačnost: 70.0%

## 📈 Analiza Performansi

### Najslabije Oblasti (zahteva dodatnu vežbu):
- Segment 3: 33.3% tačnost
- Segment 5: 50.0% tačnost
- Segment 1: 66.7% tačnost
```

## 🐛 Troubleshooting

### Problem: "GOOGLE_API_KEY nije postavljen"
**Rešenje**: Proverite da li je `.env` fajl kreiran i da sadrži validan Google API ključ.

### Problem: PDF se ne parsira
**Rešenje**: Aplikacija automatski pokušava sa alternativnim parserom. Ako i dalje ne radi, proverite da li je PDF zaštićen lozinkom ili oštećen.

### Problem: Previše dugo generisanje pitanja
**Rešenje**: Smanjite broj pitanja ili veličinu segmenta. Google Gemini API ima rate limits.

### Problem: Greška pri generisanju pitanja
**Rešenje**: Proverite internet konekciju i da li je Google API ključ validan. Proverite da li imate dovoljno quota na Google Cloud.

## 🔮 Buduća Poboljšanja

- [ ] Podrška za lokalne LLM-ove (Ollama, LM Studio)


## 📝 Licenca

Ovaj projekat je kreiran za edukativne svrhe. Slobodno koristite i modifikujte prema potrebama.

## 🤝 Kontakt

Za pitanja ili sugestije, otvorite issue ili kontaktirajte developera.

---

