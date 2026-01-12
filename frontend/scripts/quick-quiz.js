// Quick Quiz JavaScript
// =====================

// API_BASE_URL is already defined in common.js

function handleQuickQuizSubmit(e) {
    console.log('🔵 QUICK-QUIZ.JS - handleQuickQuizSubmit pozvan');
    
    // Prevent default form submission
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    const topicInput = document.getElementById('quizTopic');
    const numQuestionsInput = document.getElementById('numQuestions');
    const difficultySelect = document.getElementById('difficulty');
    
    if (!topicInput || !numQuestionsInput || !difficultySelect) {
        console.error('Form inputs not found');
        alert('Greška: Forma nije pravilno učitana');
        return false;
    }
    
    const topic = topicInput.value.trim();
    const numQuestions = parseInt(numQuestionsInput.value);
    const difficulty = difficultySelect.value;
    
    console.log('Form values:', { topic, numQuestions, difficulty });
    
    // Validate inputs
    if (!topic) {
        alert('Molimo unesite temu kviza');
        topicInput.focus();
        return false;
    }
    
    if (isNaN(numQuestions) || numQuestions < 1 || numQuestions > 50) {
        alert('Broj pitanja mora biti između 1 i 50');
        numQuestionsInput.focus();
        return false;
    }
    
    // Store quiz data in sessionStorage
    const quizData = {
        topic,
        numQuestions,
        difficulty,
        type: 'quick'
    };
    
    sessionStorage.setItem('quickQuizData', JSON.stringify(quizData));
    console.log('Quiz data saved to sessionStorage:', quizData);
    
    // Verify data was saved
    const savedData = sessionStorage.getItem('quickQuizData');
    if (!savedData) {
        alert('Greška pri čuvanju podataka. Pokušajte ponovo.');
        return false;
    }
    
    // Redirect to console manager
    console.log('🔵 QUICK-QUIZ.JS - Redirecting to console-manager.html...');
    
    // Use simple relative path
    try {
        window.location.href = 'console-manager.html';
    } catch (err) {
        console.error('🔵 QUICK-QUIZ.JS - Greška pri redirect-u:', err);
        alert('Greška pri preusmjeravanju. Pokušajte ponovo.');
    }
    
    return false;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔵 QUICK-QUIZ.JS - DOMContentLoaded pozvan');
    
    // Check auth (bez JWT)
    if (typeof checkAuth === 'function') {
        if (!checkAuth()) {
            console.warn('🔵 QUICK-QUIZ.JS - checkAuth() vratio false, preusmjeravam na login');
            return;
        }
        console.log('🔵 QUICK-QUIZ.JS - checkAuth() prošao');
    } else {
        console.error('🔵 QUICK-QUIZ.JS - checkAuth nije dostupan!');
        const userData = localStorage.getItem('userData');
        if (!userData) {
            console.warn('🔵 QUICK-QUIZ.JS - Nema userData, preusmjeravam na login');
            window.location.href = "../pages/login.html";
            return;
        }
    }
    
    const form = document.getElementById('quickQuizForm');
    if (!form) {
        console.error('🔵 QUICK-QUIZ.JS - Form not found!');
        return;
    }
    
    console.log('🔵 QUICK-QUIZ.JS - Form found, adding event listeners');
    
    // Add submit event listener to form
    form.addEventListener('submit', function(e) {
        console.log('🔵 QUICK-QUIZ.JS - Form submit event');
        e.preventDefault();
        e.stopPropagation();
        handleQuickQuizSubmit(e);
        return false;
    });
    
    // Add click listener to submit button
    const submitBtn = document.getElementById('generateQuizBtn');
    if (submitBtn) {
        console.log('🔵 QUICK-QUIZ.JS - Submit button found, adding click listener');
        submitBtn.addEventListener('click', function(e) {
            console.log('🔵 QUICK-QUIZ.JS - Generate button clicked');
            e.preventDefault();
            e.stopPropagation();
            handleQuickQuizSubmit(e);
            return false;
        });
    } else {
        console.error('🔵 QUICK-QUIZ.JS - Submit button not found!');
    }
    
    console.log('🔵 QUICK-QUIZ.JS - Event listeners added');
});

