// My Quizzes JavaScript
// =====================
// checkAuth je već definisan u common.js
// API_BASE_URL je već definisan u common.js

console.log('🟣 MY-QUIZZES.JS SE UČITAVA!');

async function loadQuizzes() {
    console.log('🟣 MY-QUIZZES.JS - loadQuizzes() pozvan');
    
    const container = document.getElementById('quizzesContainer');
    const emptyState = document.getElementById('emptyState');
    const viewResultsSection = document.getElementById('viewResultsSection');
    
    if (!container) {
        console.error('🟣 MY-QUIZZES.JS - quizzesContainer nije pronađen!');
        return;
    }
    
    container.innerHTML = '<div class="loading">Učitavanje kvizova...</div>';
    
    try {
        // Koristi getUserData iz common.js
        let userData;
        if (typeof getUserData === 'function') {
            console.log('🟣 MY-QUIZZES.JS - Koristim getUserData() iz common.js');
            userData = getUserData();
        } else {
            console.warn('🟣 MY-QUIZZES.JS - getUserData() nije dostupan, koristim direktno localStorage');
            userData = JSON.parse(localStorage.getItem('userData') || '{}');
        }
        
        if (!userData || !userData.id) {
            console.error('🟣 MY-QUIZZES.JS - Nema userData ili user ID');
            container.innerHTML = '<div class="error">Niste prijavljeni. Molimo prijavite se ponovo.</div>';
            return;
        }
        
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        console.log('🟣 MY-QUIZZES.JS - Šaljem zahtev na:', `${apiUrl}/api/my_quizzes?user_id=${userData.id}`);
        
        const response = await fetch(`${apiUrl}/api/my_quizzes?user_id=${userData.id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('🟣 MY-QUIZZES.JS - Response status:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('🟣 MY-QUIZZES.JS - Greška pri učitavanju kvizova:', error);
            container.innerHTML = `<div class="error">Greška pri učitavanju kvizova: ${error.error || 'Nepoznata greška'}</div>`;
            return;
        }
        
        const quizzes = await response.json();
        console.log('🟣 MY-QUIZZES.JS - Primljeni kvizovi:', quizzes);
        
        if (!quizzes || quizzes.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            if (viewResultsSection) viewResultsSection.style.display = 'none';
        } else {
            container.innerHTML = '';
            if (emptyState) emptyState.style.display = 'none';
            if (viewResultsSection) viewResultsSection.style.display = 'block';
            
            // Renderuj kvizove
            quizzes.forEach(quiz => {
                const quizCard = document.createElement('div');
                quizCard.className = 'quiz-card';
                
                // Kreiraj dugmad sa event listenerima umesto onclick atributa
                const startBtn = document.createElement('button');
                startBtn.className = 'btn btn-primary';
                startBtn.textContent = 'Pokreni Kviz';
                startBtn.addEventListener('click', () => {
                    console.log('🟣 MY-QUIZZES.JS - Start button kliknut za quiz ID:', quiz.id);
                    startQuiz(quiz.id);
                });
                
                const viewResultsBtn = document.createElement('button');
                viewResultsBtn.className = 'btn btn-secondary';
                viewResultsBtn.textContent = 'Pogledaj Rezultate';
                viewResultsBtn.addEventListener('click', () => {
                    console.log('🟣 MY-QUIZZES.JS - View Results button kliknut za quiz ID:', quiz.id);
                    viewResults(quiz.id);
                });
                
                quizCard.innerHTML = `
                    <div class="quiz-card-header">
                        <h3>${quiz.title || 'Kviz bez naslova'}</h3>
                        <span class="quiz-status ${quiz.status || 'draft'}">${quiz.status || 'draft'}</span>
                    </div>
                    <div class="quiz-card-body">
                        <p class="quiz-info">
                            <span>📝 ${quiz.num_questions || 0} pitanja</span>
                            <span>📅 ${new Date(quiz.created_at).toLocaleDateString('sr-RS')}</span>
                        </p>
                    </div>
                    <div class="quiz-card-actions">
                    </div>
                `;
                
                // Dodaj dugmad u actions div
                const actionsDiv = quizCard.querySelector('.quiz-card-actions');
                actionsDiv.appendChild(startBtn);
                actionsDiv.appendChild(viewResultsBtn);
                
                container.appendChild(quizCard);
            });
        }
    } catch (error) {
        console.error('🟣 MY-QUIZZES.JS - Error loading quizzes:', error);
        container.innerHTML = `<div class="error">Greška pri učitavanju kvizova: ${error.message}</div>`;
    }
}

function startQuiz(quizId) {
    console.log('🟣 MY-QUIZZES.JS - startQuiz() pozvan za quiz ID:', quizId);
    // Preusmeri na quiz-take stranicu
    window.location.href = `quiz-take.html?quiz_id=${quizId}`;
}

function viewResults(quizId) {
    console.log('🟣 MY-QUIZZES.JS - viewResults() pozvan za quiz ID:', quizId);
    // Preusmeri na quiz results stranicu
    window.location.href = `quiz-results.html?quiz_id=${quizId}`;
}

// Eksportuj funkcije na window objekat da budu dostupne globalno
window.startQuiz = startQuiz;
window.viewResults = viewResults;

document.addEventListener('DOMContentLoaded', function() {
    // checkAuth je iz common.js
    if (typeof checkAuth === 'function') {
        if (!checkAuth()) return;
    } else {
        console.error('checkAuth nije dostupan iz common.js!');
        return;
    }
    loadQuizzes();
});

