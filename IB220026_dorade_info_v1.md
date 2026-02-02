IB220026_dorade_info_v1
========================

Datum: 2026-02-03
Autor: Automatski generisan tehnički izvještaj
Stil: Tehnički, jasan, akademski

Uvod
-----
Dokument sažeto i formalno opisuje dvije obavezne dorade backend sistema: 

1. Implementaciju autonomnog background runnera (worker loop + tick + NoWork),
2. Transformaciju web sloja u "thin web" — premještanje poslovne logike iz `api_server.py` u servisni sloj (`application/quiz_service.py`).

Za svaku stavku dokument sadrži: (1) Šta je bilo prije, (2) Šta je poslije, (3) Gdje se promjena vidi u kodu (putanja / fajl / klasa / metoda). Numeracija odgovara originalnoj numeraciji zahtjeva.

Verifikacija trenutnog stanja
-----------------------------
- Implementirano: DB-backed job queue, `Runner` koji poziva `tick()` i vraća `NoWork` kad nema posla, osnovni servisni sloj (`QuizService`) te refaktoriran `api_server.py` za ključne endpoint-e. ✅
- Implementirano: queue je DB-backed (SQLite) i podržava atomarno claim-ovanje; retry/backoff mehanika na nivou jobova je implementirana. ✅
- Implementirano: endpoint `/api/upload_pdf` sada radi kao thin web—sadržaj se sprema u temp fajl i uredi se background `parse_and_chunk` job (job enqueue). Parsiranje i chunking su premješteni u `UploadService.parse_and_chunk_pdf` i obrađuju se u background workeru. Dodat je endpoint `GET /api/job/<id>` za provjeru statusa i rezultata job-a. ✅


1) Implementirati background runner (loop/worker) + tick + NoWork stanje
------------------------------------------------------------------------

1) Šta je bilo prije
- Aplikacija je bila pokretana iz `backend/main.py` koji samo poziva `launch_ui(...)` i ne startuje nijedan background consumer ili worker. Svi intenzivni procesi (generisanje pitanja, LLM pozivi) su inicirani direktno iz HTTP zahtjeva (web layer). Ovo onemogućava autonomno, agent-like ponašanje i otežava asinkrono procesiranje poslova.

2) Šta je poslije
- Uveden je autonomni background worker (`Runner`) koji kontinuirano izvodi loop i poziva `tick()` kako bi procesirao tačno jedan posao po tick-u. Ako nema posla, `tick()` vraća stanje `NoWork`, pa runner primjenjuje poll interval/backoff prije sljedećeg pokušaja.
- Jobs su predstavljeni entitetima (`Job`) s metapodacima (payload, retries, max_retries, status itd.). Postoji DB-backed queue (tabela `jobs`) koja omogućava perzistentnost poslova i atomarno claim-ovanje.
- `Runner` radi nezavisno od web requestova; podržan je graceful shutdown (stop signal pri prekidu aplikacije).

Kratki pseudokod (konceptualno):
```
async def tick():
    job = JobQueue.claim_next_job()
    if not job:
        return NoWork
    try:
        result = QuizService.process_job(job)
        JobQueue.mark_done(job, result)
        return Success
    except Exception:
        JobQueue.mark_failed(job)
        return Failure
```

3) Gdje se promjena vidi u kodu
- `backend/background/runner.py` — klasa `Runner` (metode: `start()`, `stop()`, `_run()`, `tick()`).
- `backend/infra/job_queue.py` — `JobQueue` (metode: `create_job`, `claim_next_job`, `mark_done`, `mark_failed`, `get_job`) i atomarno claim-ovanje (`BEGIN IMMEDIATE` u SQLite transakciji).
- `backend/models/job.py` — `Job` model i `JobStatus` enum (PENDING, IN_PROGRESS, DONE, FAILED).
- `backend/database.py` — nova tabela `jobs` u inicijalizaciji baze.
- `backend/main.py` — komponenta koja inicira i startuje `Runner` pri pokretanju aplikacije (startup hook) i poziva `runner.stop()` kod gašenja.

Komentar o validaciji implementacije
- Lokalno testiranje je pokazalo da runner atomarno claim-uje i procesira job; retry logika radi (job prelazi u PENDING ili FAILED ovisno o retry count). 
- Potrebno je osigurati da env varijable (npr. `GOOGLE_API_KEY`) budu dostupne background procesu da bi job-ovi koji pozivaju LLM uspješno prošli.


2) Napraviti thin web layer (premjestiti poslovnu logiku u servisni sloj)
------------------------------------------------------------------------

1) Šta je bilo prije
- `backend/api_server.py` sadrži značajnu količinu poslovne logike: parsing PDF-a, chunking, direktne LLM pozive (`GeminiQuestionGenerator`), sekvencijalnu orkestraciju (korištenje `QuizEngine`/`RLAgent`) i implementaciju SSE stream-a. Web sloj je odgovoran za obradu, što otežava testiranje i održavanje.

2) Šta je poslije
- Uveden je servisni sloj `backend/application/quiz_service.py` koji centralizira poslovnu logiku (generisanje pitanja, orkestracija, pozivi LLM modelu, eventualno persistencija rezultata). API endpointi su refaktorisani tako da rade *isključivo* sljedeće:
  - Validacija inputa,
  - Pozivanje servisnih metoda (`QuizService.generate_question_from_chunk`, `QuizService.generate_questions`, itd.),
  - Vraćanje odgovora ili enqueue posla u job queue za asinkrono procesiranje.
- Dodan je endpoint za enqueue background job-a: `POST /api/enqueue_generate_questions` koji stvara `generate_next_question` job u queue-u.

Kratki pseudokod (konceptualno):
```
@app.post('/sessions/{id}/next')
def next_question(id):
    validate(id)
    # thin: poziva servisnu funkciju
    res = QuizService.generate_next_question(session_id=id)
    return res
```

3) Gdje se promjena vidi u kodu
- `backend/application/quiz_service.py` — glavna orkestracija poslovne logike (`generate_question_from_chunk`, `generate_questions`, `process_job`). Ovdje su centralizovani pozivi prema `google_gemini_generator.py`, `quiz_engine.py`, `rl_agent.py`.
- `backend/api_server.py` — endpointi `generate_question_from_chunk` i `generate_questions` sada delegiraju na `QuizService` (thin web). Dodan endpoint `enqueue_generate_questions` za stavljanje posla u queue (`JobQueue.create_job`).
- Postojeći util moduli (`chunking.py`, `embeddings.py`, `question_generator.py`, `google_gemini_generator.py`) su zadržani kao helperi koji se koriste iz `QuizService`, ne direktno iz web sloja za nove tokove.

Napomena o preostalom radu
- `POST /api/upload_pdf` je refaktorisano: endpoint sada samo sprema upload i enqueue-uje `parse_and_chunk` job; parsiranje i chunking su premješteni u `application/upload_service.py` i obrađuju se u background workeru. UploadService persisitira chunks u `quizzes` tabelu (status=`processing`) i automatski enqueue-uje `generate_next_question` job za daljnju obradu. Preporučeno: dodati politiku čišćenja privremenih fajlova nakon obrade i health/metrics za praćenje background procesa i jobova.


Zaključak i preporuke za dovršetak
----------------------------------
- Da, glavne tražene dorade (autonomni background runner i thin web layer) su implementirane i integrisane u backend projekt. ✅
- Preporuke za dovršetak i poboljšanje:
  - Premjestiti chunking i SSE logiku iz `api_server.py` u servis (`application/upload_service.py` ili proširiti `QuizService`) i koristiti background jobs za intenzivne tokove.
  - Dodati health/metrics endpoint za runner i queue (npr. `/api/worker/health`, `/api/job/<id>`), i osnovne Prometheus metrike.
  - Pokriti `JobQueue`, `Runner` i `QuizService` unit i integration testovima.
  - Razmotriti migraciju queue-a na Redis/RabbitMQ za horizontalno skaliranje i bolju konkurentnost.


Sljedeći koraci (predloženo)
-----------------------------
1. (Dovršeno) `upload_pdf` je premješten u servis i enqueuing procesa je omogućen (prioritet: visok). ✅
2. Dodati health/metrics i testove (prioritet: srednji). 
3. Opcionalno: podrška za vanjski queue (Redis) i worker pool za horizontalno skaliranje (prioritet: niski do srednji, ovisno o opterećenju).


Prilozi: mapa promjena (kratko)
- Nova/funkcionalna mesta u repozitoriju:
  - `backend/models/job.py`  (Job model)
  - `backend/infra/job_queue.py`  (DB-backed queue)
  - `backend/background/runner.py` (Runner loop + tick)
  - `backend/background/manager.py` (Singleton runner manager za health)
  - `backend/application/quiz_service.py` (servisni sloj za poslovnu logiku)
  - `backend/application/upload_service.py` (upload parsing & chunking)
  - `backend/main.py` (start runner pri pokretanju)
  - `backend/api/api_server.py` (refaktorisani endpointi, `enqueue_generate_questions`, job status i worker health endpoint)

Struktura i organizacija fajlova (nova)
- `backend/core/` — core library: `pdf_parser.py`, `chunking.py`, `quiz_engine.py`, `question_generator.py`, `rl_agent.py` (poslovna logika i helperi)
- `backend/llm/` — LLM klijenti i embeddings: `google_gemini_generator.py`, `embeddings.py`
- `backend/services/` — pomoćne usluge: `charts.py`, `export_results.py`
- `backend/auth/` — autentifikacija: `auth.py`, `auth_api.py`
- `backend/background/` — runner i manager: `runner.py`, `manager.py`
- `backend/api/` — REST API server: `api_server.py`

-- Kraj dokumenta --
