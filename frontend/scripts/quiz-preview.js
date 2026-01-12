// Quiz Preview JavaScript
// =======================

// API_BASE_URL is already defined in common.js

console.log('🟡 QUIZ-PREVIEW.JS SE UČITAVA!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🟡 QUIZ-PREVIEW.JS - DOMContentLoaded pozvan');
    
    // Check auth (bez JWT)
    if (typeof checkAuth === 'function') {
        console.log('🟡 QUIZ-PREVIEW.JS - checkAuth je dostupan');
        if (!checkAuth()) {
            console.warn('🟡 QUIZ-PREVIEW.JS - checkAuth() vratio false, prekidam');
            return;
        }
        console.log('🟡 QUIZ-PREVIEW.JS - checkAuth() prošao');
    } else {
        console.error('🟡 QUIZ-PREVIEW.JS - checkAuth nije dostupan!');
        const userData = localStorage.getItem('userData');
        if (!userData) {
            console.warn('🟡 QUIZ-PREVIEW.JS - Nema userData, preusmjeravam na login');
            window.location.href = '../pages/login.html';
            return;
        }
    }
    
    const quizData = JSON.parse(sessionStorage.getItem('generatedQuiz') || '{}');
    console.log('🟡 QUIZ-PREVIEW.JS - Quiz data iz sessionStorage:', quizData);
    
    if (!quizData.questions || quizData.questions.length === 0) {
        console.warn('🟡 QUIZ-PREVIEW.JS - Nema pitanja u quizData, preusmjeravam na create-quiz');
        window.location.href = 'create-quiz.html';
        return;
    }
    
    console.log('🟡 QUIZ-PREVIEW.JS - Prikazujem kviz sa', quizData.questions.length, 'pitanja');
    displayQuiz(quizData);
    
    const saveBtn = document.getElementById('saveQuizBtn');
    if (saveBtn) {
        console.log('🟡 QUIZ-PREVIEW.JS - Save button pronađen, dodajem event listener');
        saveBtn.addEventListener('click', () => saveQuiz(quizData));
    } else {
        console.error('🟡 QUIZ-PREVIEW.JS - Save button nije pronađen!');
    }
});

function displayQuiz(quizData) {
    // Prikaži naslov kviza
    const titleEl = document.getElementById('quizTitle');
    if (titleEl) {
        titleEl.textContent = `👁️ ${quizData.title || 'Preview Kviza'}`;
    }
    
    // Prikaži dodatne informacije
    const subtitleEl = document.getElementById('quizSubtitle');
    if (subtitleEl) {
        subtitleEl.textContent = `Pregledajte ${quizData.questions?.length || 0} generisanih pitanja pre nego što ga sačuvate`;
    }
    
    const previewContainer = document.getElementById('questionsPreview');
    if (!previewContainer) {
        console.error('🟡 QUIZ-PREVIEW.JS - questionsPreview container nije pronađen!');
        return;
    }
    
    previewContainer.innerHTML = '';
    
    if (!quizData.questions || quizData.questions.length === 0) {
        previewContainer.innerHTML = '<p style="color: var(--theme-text-secondary, #B3B3B3); text-align: center; padding: 2rem;">Nema pitanja za prikaz.</p>';
        return;
    }
    
    console.log('🟡 QUIZ-PREVIEW.JS - Prikazujem', quizData.questions.length, 'pitanja');
    
    quizData.questions.forEach((question, index) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'question-preview-item';
        questionDiv.style.cssText = 'margin-bottom: 2rem; padding: 1.5rem; background: #2F2F2F; border-radius: 8px; border-left: 4px solid var(--theme-primary, #E50914);';
        
        // Formatiraj opcije
        const optionsHtml = question.options ? Object.entries(question.options).map(([key, value]) => {
            const isCorrect = key === question.correct_answer;
            return `
                <div style="padding: 0.75rem; background: #1a1a1a; border-radius: 4px; color: var(--theme-text-secondary, #B3B3B3); ${isCorrect ? 'border: 2px solid #00ff00;' : ''}">
                    <strong>${key}:</strong> ${value}
                    ${isCorrect ? ' <span style="color: #00ff00; font-weight: bold;">✓ Tačan odgovor</span>' : ''}
                </div>
            `;
        }).join('') : '<p style="color: #ff6b6b;">Nema opcija za ovo pitanje</p>';
        
        questionDiv.innerHTML = `
            <h3 style="color: var(--theme-text, #FFFFFF); margin-bottom: 1rem; font-size: 1.2rem;">
                Pitanje ${index + 1}: ${question.question || 'N/A'}
            </h3>
            <div class="options-preview" style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem;">
                ${optionsHtml}
            </div>
            ${question.explanation ? `
                <div style="padding: 1rem; background: #1a1a1a; border-radius: 4px; color: var(--theme-text-secondary, #B3B3B3); margin-top: 1rem;">
                    <strong style="color: var(--theme-primary, #E50914);">💡 Objašnjenje:</strong> 
                    <span style="margin-left: 0.5rem;">${question.explanation}</span>
                </div>
            ` : ''}
        `;
        
        previewContainer.appendChild(questionDiv);
    });
    
    console.log('🟡 QUIZ-PREVIEW.JS - Sva pitanja su prikazana');
}

async function saveQuiz(quizData) {
    console.log('🟡 QUIZ-PREVIEW.JS - saveQuiz() pozvan');
    
    const saveBtn = document.getElementById('saveQuizBtn');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Čuvanje...';
    }
    
    try {
        // Koristi getUserData iz common.js
        let userData;
        if (typeof getUserData === 'function') {
            console.log('🟡 QUIZ-PREVIEW.JS - Koristim getUserData() iz common.js');
            userData = getUserData();
        } else {
            console.warn('🟡 QUIZ-PREVIEW.JS - getUserData() nije dostupan, koristim direktno localStorage');
            userData = JSON.parse(localStorage.getItem('userData') || '{}');
        }
        
        console.log('🟡 QUIZ-PREVIEW.JS - User data:', userData);
        
        if (!userData || !userData.id) {
            console.error('🟡 QUIZ-PREVIEW.JS - Nema userData ili user ID');
            alert('Niste prijavljeni. Molimo prijavite se ponovo.');
            window.location.href = '../pages/login.html';
            return;
        }
        
        console.log('🟡 QUIZ-PREVIEW.JS - Šaljem zahtev za čuvanje kviza...');
        const response = await fetch(`${API_BASE_URL}/api/save_quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userData.id,
                title: quizData.title,
                topic: quizData.topic,
                questions: quizData.questions,
                difficulty: quizData.difficulty,
                type: quizData.type || 'quick'
            })
        });
        
        console.log('🟡 QUIZ-PREVIEW.JS - Response status:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('🟡 QUIZ-PREVIEW.JS - Greška pri čuvanju:', error);
            throw new Error(error.error || 'Greška pri čuvanju kviza');
        }
        
        const result = await response.json();
        console.log('🟡 QUIZ-PREVIEW.JS - Kviz uspešno sačuvan:', result);
        alert('Kviz je uspešno sačuvan!');
        window.location.href = 'my-quizzes.html';
        
    } catch (error) {
        alert('Greška pri čuvanju kviza: ' + error.message);
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.textContent = '💾 Sačuvaj Kviz';
        }
    }
}

