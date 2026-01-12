@echo off
echo Pokretanje REST API servera...
echo.
echo Otvaranje index.html u browseru...
start "" "frontend\pages\index.html"
echo.
echo Cekanje 3 sekunde da se browser otvori...
timeout /t 3 /nobreak >nul
echo.
cd backend
python api_server.py
pause

