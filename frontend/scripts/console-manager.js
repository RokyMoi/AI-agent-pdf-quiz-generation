// Console Manager JavaScript
// ===========================

// API_BASE_URL is already defined in common.js (ne deklariši ga ponovo!)

console.log('🟠 CONSOLE-MANAGER.JS SE UČITAVA!');
console.log('🟠 CONSOLE-MANAGER.JS - API_BASE_URL:', typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'NEDEFINISAN');

let currentQuestion = 0;
let generatedQuestions = [];

function addConsoleLog(message, type = 'info') {
    const consoleOutput = document.getElementById('consoleOutput');
    if (!consoleOutput) {
        console.error('🟠 CONSOLE-MANAGER.JS - consoleOutput element nije pronađen!');
        return;
    }
    
    const line = document.createElement('div');
    line.className = 'console-line';
    
    const prompt = document.createElement('span');
    prompt.className = 'console-prompt';
    prompt.textContent = '$';
    
    const text = document.createElement('span');
    text.className = `console-text ${type}`;
    text.textContent = message;
    
    line.appendChild(prompt);
    line.appendChild(text);
    consoleOutput.appendChild(line);
    
    // Auto scroll to bottom
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
    
    console.log(`🟠 CONSOLE-MANAGER.JS - addConsoleLog: ${message}`);
}

function updateProgress(percent, status) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    
    if (progressBar) progressBar.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = percent + '%';
    if (progressStatus) progressStatus.textContent = status;
}

function updateStatus(text, type = 'info') {
    const statusText = document.getElementById('statusText');
    const statusDot = document.querySelector('.status-dot');
    
    if (statusText) statusText.textContent = text;
    if (statusDot) {
        statusDot.className = 'status-dot';
        if (type === 'complete') statusDot.classList.add('complete');
        if (type === 'error') statusDot.classList.add('error');
    }
}

async function startQuizGeneration(quizData) {
    console.log('🟠 CONSOLE-MANAGER.JS - startQuizGeneration() pozvan sa:', quizData);
    
    try {
        console.log('🟠 CONSOLE-MANAGER.JS - Dodajem log: Sistem inicijalizovan...');
        addConsoleLog('Sistem inicijalizovan...', 'info');
        await sleep(500);
        console.log('🟠 CONSOLE-MANAGER.JS - Sleep završen, nastavljam...');
    } catch (error) {
        console.error('🟠 CONSOLE-MANAGER.JS - Greška na početku startQuizGeneration:', error);
        throw error;
    }
    
    addConsoleLog(`Tema kviza: ${quizData.topic}`, 'info');
    addConsoleLog(`Broj pitanja: ${quizData.numQuestions}`, 'info');
    addConsoleLog(`Težina: ${quizData.difficulty}`, 'info');
    await sleep(500);
    
    addConsoleLog('Povezivanje sa Gemini API...', 'info');
    updateProgress(10, 'Povezivanje...');
    await sleep(1000);
    
    addConsoleLog('✓ Povezano sa Gemini API', 'success');
    await sleep(500);
    
    console.log(`🟠 CONSOLE-MANAGER.JS - Počinjem generisanje ${quizData.numQuestions} pitanja...`);
    
    // Generate questions one by one
    for (let i = 0; i < quizData.numQuestions; i++) {
        currentQuestion = i + 1;
        const progress = 10 + ((i + 1) / quizData.numQuestions) * 80;
        
        console.log(`🟠 CONSOLE-MANAGER.JS - Generišem pitanje ${currentQuestion}/${quizData.numQuestions}...`);
        addConsoleLog(`Generišem pitanje ${currentQuestion}/${quizData.numQuestions}...`, 'info');
        updateProgress(Math.floor(progress), `Generisanje pitanja ${currentQuestion}...`);
        
        try {
            console.log(`🟠 CONSOLE-MANAGER.JS - Pozivam generateQuestion() za pitanje ${currentQuestion}...`);
            const question = await generateQuestion(quizData.topic, quizData.difficulty, i + 1);
            console.log(`🟠 CONSOLE-MANAGER.JS - Pitanje ${currentQuestion} uspešno generisano:`, question);
            
            generatedQuestions.push(question);
            
            addConsoleLog(`✓ Pitanje ${currentQuestion} uspešno generisano`, 'success');
            await sleep(800);
        } catch (error) {
            const errorMsg = error.message || 'Nepoznata greška';
            console.error(`🟠 CONSOLE-MANAGER.JS - Greška pri generisanju pitanja ${currentQuestion}:`, error);
            addConsoleLog(`✗ Greška pri generisanju pitanja ${currentQuestion}: ${errorMsg}`, 'error');
            
            // If it's an API key or model availability error, stop generation
            if (errorMsg.includes('API key') || errorMsg.includes('Model nije dostupan') || errorMsg.includes('404')) {
                addConsoleLog('⚠️ Zaustavljam generisanje zbog API greške. Proverite API key i dostupnost modela.', 'error');
                updateStatus('Greška - Proverite API key', 'error');
                updateProgress(0, 'Zaustavljeno');
                return;
            }
            
            await sleep(1000); // Wait longer on error
        }
    }
    
    addConsoleLog('✓ Sva pitanja uspešno generisana!', 'success');
    updateProgress(100, 'Završeno');
    updateStatus('Uspešno generisano', 'complete');
    
    await sleep(1000);
    
    // Store generated quiz and redirect
    sessionStorage.setItem('generatedQuiz', JSON.stringify({
        title: `Kviz: ${quizData.topic}`,
        topic: quizData.topic,
        questions: generatedQuestions,
        difficulty: quizData.difficulty,
        type: 'quick'
    }));
    
    addConsoleLog('Preusmeravanje na preview...', 'info');
    await sleep(1000);
    
    window.location.href = 'quiz-preview.html';
}

async function generateQuestion(topic, difficulty, questionNum) {
    console.log(`🟠 CONSOLE-MANAGER.JS - generateQuestion() pozvan za pitanje ${questionNum}`);
    console.log(`🟠 CONSOLE-MANAGER.JS - Topic: ${topic}, Difficulty: ${difficulty}`);
    
    try {
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        console.log(`🟠 CONSOLE-MANAGER.JS - Šaljem zahtev na: ${apiUrl}/api/generate_quick_question`);
        
        // Dodaj timeout za fetch (90 sekundi - povećano zbog rate limiting delay-a)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 90000);
        
        let response;
        try {
            response = await fetch(`${apiUrl}/api/generate_quick_question`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic,
                    difficulty: difficulty,
                    question_number: questionNum
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (fetchError) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
                throw new Error('Zahtev je prekoračio vreme čekanja (60 sekundi). Proverite API server.');
            }
            throw new Error(`Greška pri povezivanju sa serverom: ${fetchError.message}`);
        }
        
        console.log(`🟠 CONSOLE-MANAGER.JS - Response status: ${response.status}`);
        
        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: `HTTP ${response.status}: ${response.statusText}` };
            }
            
            const errorMsg = errorData.error || `HTTP ${response.status}: ${response.statusText}`;
            
            // Check for specific error types
            if (response.status === 400 && errorMsg.includes('API key')) {
                throw new Error('API key greška. Proverite GOOGLE_API_KEY u .env fajlu.');
            } else if (response.status === 429) {
                throw new Error('Rate limit prekoračen. Sačekajte malo i pokušajte ponovo.');
            } else if (response.status === 404) {
                throw new Error('Model nije dostupan. Proverite da li vaš API key ima pristup Gemini modelima.');
            } else {
                throw new Error(errorMsg);
            }
        }
        
        const question = await response.json();
        console.log(`🟠 CONSOLE-MANAGER.JS - Pitanje primljeno:`, question);
        
        // Validate question structure
        if (!question || !question.question || !question.options) {
            console.error('🟠 CONSOLE-MANAGER.JS - Neispravan format pitanja:', question);
            throw new Error('Neispravan format pitanja od API-ja');
        }
        
        console.log(`🟠 CONSOLE-MANAGER.JS - Pitanje ${questionNum} validirano i vraćeno`);
        return question;
    } catch (error) {
        console.error('🟠 CONSOLE-MANAGER.JS - Error generating question:', error);
        throw error;
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🟠 CONSOLE-MANAGER.JS - DOMContentLoaded pozvan');
    
    // Check auth (bez JWT)
    if (typeof checkAuth === 'function') {
        console.log('🟠 CONSOLE-MANAGER.JS - checkAuth je dostupan');
        if (!checkAuth()) {
            console.warn('🟠 CONSOLE-MANAGER.JS - checkAuth() vratio false, prekidam');
            return;
        }
        console.log('🟠 CONSOLE-MANAGER.JS - checkAuth() prošao');
    } else {
        console.error('🟠 CONSOLE-MANAGER.JS - checkAuth nije dostupan!');
        const userData = localStorage.getItem('userData');
        if (!userData) {
            console.warn('🟠 CONSOLE-MANAGER.JS - Nema userData, preusmjeravam na login');
            window.location.href = '../pages/login.html';
            return;
        }
    }
    
    const quizData = JSON.parse(sessionStorage.getItem('quickQuizData') || '{}');
    console.log('🟠 CONSOLE-MANAGER.JS - Quiz data iz sessionStorage:', quizData);
    
    if (!quizData.topic) {
        console.error('🟠 CONSOLE-MANAGER.JS - No quiz data found, redirecting to quick-quiz.html');
        window.location.href = 'quick-quiz.html';
        return;
    }
    
    console.log('🟠 CONSOLE-MANAGER.JS - Starting quiz generation with data:', quizData);
    console.log('🟠 CONSOLE-MANAGER.JS - API_BASE_URL:', typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'NEDEFINISAN');
    
    // Start generation
    console.log('🟠 CONSOLE-MANAGER.JS - Pozivam startQuizGeneration()...');
    startQuizGeneration(quizData).catch(error => {
        console.error('🟠 CONSOLE-MANAGER.JS - Fatal error in startQuizGeneration:', error);
        addConsoleLog(`✗ Fatalna greška: ${error.message}`, 'error');
        updateStatus('Greška', 'error');
    });
});

