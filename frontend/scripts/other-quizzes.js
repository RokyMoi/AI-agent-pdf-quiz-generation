// Other Quizzes JavaScript
// ========================
// API_BASE_URL is already defined in common.js

console.log('🟡 OTHER-QUIZZES.JS SE UČITAVA!');

async function loadQuizzes() {
    console.log('🟡 OTHER-QUIZZES.JS - loadQuizzes() pozvan');
    
    const container = document.getElementById('quizzesContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (!container) {
        console.error('🟡 OTHER-QUIZZES.JS - quizzesContainer nije pronađen!');
        return;
    }
    
    container.innerHTML = '<div class="loading">Učitavanje kvizova...</div>';
    if (emptyState) emptyState.style.display = 'none';
    
    try {
        const userData = getUserData();
        if (!userData || !userData.id) {
            console.error('🟡 OTHER-QUIZZES.JS - Nema userData');
            container.innerHTML = '<div class="error">Niste prijavljeni. Molimo prijavite se ponovo.</div>';
            return;
        }
        
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        console.log('🟡 OTHER-QUIZZES.JS - Šaljem zahtev na:', `${apiUrl}/api/public_quizzes?user_id=${userData.id}`);
        
        const response = await fetch(`${apiUrl}/api/public_quizzes?user_id=${userData.id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('🟡 OTHER-QUIZZES.JS - Response status:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('🟡 OTHER-QUIZZES.JS - Greška pri učitavanju kvizova:', error);
            container.innerHTML = `<div class="error">Greška pri učitavanju kvizova: ${error.error || 'Nepoznata greška'}</div>`;
            return;
        }
        
        const quizzes = await response.json();
        console.log('🟡 OTHER-QUIZZES.JS - Primljeni kvizovi:', quizzes);
        
        if (!quizzes || quizzes.length === 0) {
            container.innerHTML = '';
            if (emptyState) {
                emptyState.innerHTML = `
                    <div class="empty-icon">🔍</div>
                    <h2>Drugi korisnici nisu napravili kvizove</h2>
                    <p>Trenutno nema dostupnih kvizova koje su kreirali drugi korisnici</p>
                `;
                emptyState.style.display = 'block';
            }
        } else {
            container.innerHTML = '';
            if (emptyState) emptyState.style.display = 'none';
            
            // Renderuj kvizove
            quizzes.forEach(quiz => {
                const quizCard = document.createElement('div');
                quizCard.className = 'quiz-card';
                quizCard.innerHTML = `
                    <div class="quiz-card-header">
                        <h3>${quiz.title || 'Kviz bez naslova'}</h3>
                        <span class="quiz-author">Autor: ${quiz.username || 'N/A'}</span>
                    </div>
                    <div class="quiz-card-body">
                        <p class="quiz-info">
                            <span>📝 ${quiz.num_questions || 0} pitanja</span>
                            <span>📅 ${new Date(quiz.created_at).toLocaleDateString('sr-RS')}</span>
                        </p>
                        ${quiz.topic ? `<p class="quiz-topic">Tema: ${quiz.topic}</p>` : ''}
                    </div>
                    <div class="quiz-card-actions">
                        <button class="btn btn-primary" onclick="startQuiz(${quiz.id})">Pokreni Kviz</button>
                    </div>
                `;
                container.appendChild(quizCard);
            });
        }
    } catch (error) {
        console.error('🟡 OTHER-QUIZZES.JS - Error loading quizzes:', error);
        container.innerHTML = `<div class="error">Greška pri učitavanju kvizova: ${error.message}</div>`;
    }
}

function startQuiz(quizId) {
    console.log('🟡 OTHER-QUIZZES.JS - startQuiz() pozvan za quiz ID:', quizId);
    window.location.href = `quiz-take.html?quiz_id=${quizId}`;
}

// Eksportuj funkciju na window objekat
window.startQuiz = startQuiz;

// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('🟡 OTHER-QUIZZES.JS - DOMContentLoaded pozvan');
    
    if (typeof checkAuth === 'function') {
        if (!checkAuth()) return;
    }
    
    loadQuizzes();
    
    // Search button
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
            filterQuizzes(searchTerm);
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const searchTerm = searchInput.value.toLowerCase();
                filterQuizzes(searchTerm);
            }
        });
    }
});

function filterQuizzes(searchTerm) {
    const quizCards = document.querySelectorAll('.quiz-card');
    let visibleCount = 0;
    
    quizCards.forEach(card => {
        const title = card.querySelector('h3')?.textContent.toLowerCase() || '';
        const author = card.querySelector('.quiz-author')?.textContent.toLowerCase() || '';
        const topic = card.querySelector('.quiz-topic')?.textContent.toLowerCase() || '';
        
        if (title.includes(searchTerm) || author.includes(searchTerm) || topic.includes(searchTerm)) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show/hide empty state
    const emptyState = document.getElementById('emptyState');
    const container = document.getElementById('quizzesContainer');
    
    if (visibleCount === 0 && emptyState && container) {
        emptyState.innerHTML = `
            <div class="empty-icon">🔍</div>
            <h2>Nema pronađenih kvizova</h2>
            <p>Pokušajte sa drugim kriterijumima pretrage</p>
        `;
        emptyState.style.display = 'block';
    } else if (emptyState) {
        emptyState.style.display = 'none';
    }
}
