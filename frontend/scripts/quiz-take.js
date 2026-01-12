// Quiz Take JavaScript
// ====================
// API_BASE_URL is already defined in common.js

console.log('🟣 QUIZ-TAKE.JS SE UČITAVA!');

let currentQuiz = null;
let currentQuestionIndex = 0;
let userAnswers = [];
let startTime = null;

// Get quiz ID from URL
function getQuizIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('quiz_id');
}

// Load quiz from API
async function loadQuiz(quizId) {
    console.log('🟣 QUIZ-TAKE.JS - loadQuiz() pozvan za quiz ID:', quizId);
    
    try {
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/quiz/${quizId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Greška pri učitavanju kviza');
        }
        
        const quiz = await response.json();
        console.log('🟣 QUIZ-TAKE.JS - Kviz učitan:', quiz);
        return quiz;
    } catch (error) {
        console.error('🟣 QUIZ-TAKE.JS - Error loading quiz:', error);
        throw error;
    }
}

// Display question
function displayQuestion(question, questionIndex, totalQuestions) {
    const quizContent = document.getElementById('quizContent');
    if (!quizContent) return;
    
    // Update progress
    updateProgress(questionIndex + 1, totalQuestions);
    
    // Create question HTML
    const questionHTML = `
        <div class="question-container">
            <div class="question-header">
                <h2>Pitanje ${questionIndex + 1} od ${totalQuestions}</h2>
            </div>
            <div class="question-body">
                <p class="question-text">${question.question || 'N/A'}</p>
                <div class="options-container">
                    ${Object.entries(question.options || {}).map(([key, value]) => `
                        <label class="option-label">
                            <input type="radio" name="answer" value="${key}" class="option-radio">
                            <span class="option-text">${key}: ${value}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
            <div class="question-actions">
                <button id="submitAnswerBtn" class="btn btn-primary" disabled>Potvrdi Odgovor</button>
            </div>
        </div>
    `;
    
    quizContent.innerHTML = questionHTML;
    
    // Enable submit button when option is selected
    const radioButtons = document.querySelectorAll('.option-radio');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', () => {
            document.getElementById('submitAnswerBtn').disabled = false;
        });
    });
    
    // Submit answer handler
    document.getElementById('submitAnswerBtn').addEventListener('click', () => {
        const selectedOption = document.querySelector('input[name="answer"]:checked');
        if (selectedOption) {
            submitAnswer(selectedOption.value, question);
        }
    });
}

// Update progress bar
function updateProgress(current, total) {
    const progressFill = document.getElementById('progressFill');
    const progressCurrent = document.getElementById('progressCurrent');
    const progressTotal = document.getElementById('progressTotal');
    
    if (progressFill) {
        const percentage = (current / total) * 100;
        progressFill.style.width = percentage + '%';
    }
    if (progressCurrent) progressCurrent.textContent = current;
    if (progressTotal) progressTotal.textContent = total;
}

// Submit answer
async function submitAnswer(selectedAnswer, question) {
    console.log('🟣 QUIZ-TAKE.JS - submitAnswer() pozvan:', selectedAnswer);
    
    const isCorrect = selectedAnswer.toUpperCase() === question.correct_answer.toUpperCase();
    
    // Save answer
    userAnswers.push({
        question: question,
        user_answer: selectedAnswer,
        correct_answer: question.correct_answer,
        is_correct: isCorrect
    });
    
    // Show feedback
    showFeedback(question, selectedAnswer, isCorrect);
    
    // Wait a bit before showing next question
    setTimeout(() => {
        currentQuestionIndex++;
        if (currentQuestionIndex < currentQuiz.questions.length) {
            displayQuestion(currentQuiz.questions[currentQuestionIndex], currentQuestionIndex, currentQuiz.questions.length);
        } else {
            // Quiz completed
            showResults();
        }
    }, 2000);
}

// Show feedback
function showFeedback(question, userAnswer, isCorrect) {
    const quizContent = document.getElementById('quizContent');
    if (!quizContent) return;
    
    const feedbackHTML = `
        <div class="feedback-container ${isCorrect ? 'correct' : 'incorrect'}">
            <div class="feedback-icon">${isCorrect ? '✓' : '✗'}</div>
            <div class="feedback-message">
                <h3>${isCorrect ? 'Tačan odgovor!' : 'Netačan odgovor'}</h3>
                <p>Vaš odgovor: <strong>${userAnswer}</strong></p>
                ${!isCorrect ? `<p>Tačan odgovor: <strong>${question.correct_answer}</strong></p>` : ''}
                <div class="feedback-explanation">
                    <p><strong>Objašnjenje:</strong></p>
                    <p>${question.explanation || 'Nema objašnjenja'}</p>
                </div>
            </div>
        </div>
    `;
    
    quizContent.innerHTML = feedbackHTML;
}

// Show results
async function showResults() {
    console.log('🟣 QUIZ-TAKE.JS - showResults() pozvan');
    
    const totalQuestions = currentQuiz.questions.length;
    const correctAnswers = userAnswers.filter(a => a.is_correct).length;
    const accuracy = (correctAnswers / totalQuestions) * 100;
    const timeTaken = Math.floor((Date.now() - startTime) / 1000); // seconds
    
    // Hide quiz content
    document.getElementById('quizContent').style.display = 'none';
    
    // Show results
    const resultsDiv = document.getElementById('quizResults');
    resultsDiv.style.display = 'block';
    
    // Update stats
    document.getElementById('finalScore').textContent = correctAnswers;
    document.getElementById('finalAccuracy').textContent = accuracy.toFixed(1) + '%';
    document.getElementById('totalQuestions').textContent = totalQuestions;
    
    // Show detailed results
    const resultsDetails = document.getElementById('resultsDetails');
    resultsDetails.innerHTML = userAnswers.map((answer, index) => `
        <div class="result-item ${answer.is_correct ? 'correct' : 'incorrect'}">
            <div class="result-question">
                <h4>Pitanje ${index + 1}: ${answer.question.question}</h4>
            </div>
            <div class="result-answer">
                <p>Vaš odgovor: <strong>${answer.user_answer}</strong> ${answer.is_correct ? '✓' : '✗'}</p>
                ${!answer.is_correct ? `<p>Tačan odgovor: <strong>${answer.correct_answer}</strong></p>` : ''}
                <p class="result-explanation">${answer.question.explanation || 'Nema objašnjenja'}</p>
            </div>
        </div>
    `).join('');
    
    // Save results to backend
    await saveResults(correctAnswers, totalQuestions, accuracy, timeTaken);
}

// Save results to backend
async function saveResults(score, totalQuestions, accuracy, timeTaken) {
    console.log('🟣 QUIZ-TAKE.JS - saveResults() pozvan');
    
    try {
        const userData = getUserData();
        if (!userData || !userData.id) {
            console.error('🟣 QUIZ-TAKE.JS - Nema userData');
            return;
        }
        
        const quizId = getQuizIdFromURL();
        if (!quizId) {
            console.error('🟣 QUIZ-TAKE.JS - Nema quiz ID');
            return;
        }
        
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        
        // Get IP address (simplified - in production use proper IP detection)
        const ipAddress = '127.0.0.1'; // Placeholder
        
        const response = await fetch(`${apiUrl}/api/save_quiz_result`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                quiz_id: parseInt(quizId),
                user_id: userData.id,
                score: score,
                total_questions: totalQuestions,
                accuracy: accuracy / 100, // Convert to decimal
                answers_data: userAnswers,
                time_taken: timeTaken,
                ip_address: ipAddress
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('🟣 QUIZ-TAKE.JS - Greška pri čuvanju rezultata:', error);
            alert('Greška pri čuvanju rezultata: ' + (error.error || 'Nepoznata greška'));
        } else {
            const result = await response.json();
            console.log('🟣 QUIZ-TAKE.JS - Rezultati sačuvani:', result);
            console.log('🟣 QUIZ-TAKE.JS - Result ID:', result.result_id);
        }
    } catch (error) {
        console.error('🟣 QUIZ-TAKE.JS - Error saving results:', error);
    }
}

// Initialize quiz
async function initQuiz() {
    console.log('🟣 QUIZ-TAKE.JS - initQuiz() pozvan');
    
    // Check auth
    if (typeof checkAuth === 'function') {
        if (!checkAuth()) {
            window.location.href = '../pages/login.html';
            return;
        }
    }
    
    const quizId = getQuizIdFromURL();
    if (!quizId) {
        alert('Kviz ID nije pronađen. Preusmjeravam na Moje Kvizove...');
        window.location.href = 'my-quizzes.html';
        return;
    }
    
    try {
        // Load quiz
        currentQuiz = await loadQuiz(quizId);
        
        // Update title
        const quizTitle = document.getElementById('quizTitle');
        if (quizTitle) {
            quizTitle.textContent = currentQuiz.title || 'Kviz';
        }
        
        // Start quiz
        startTime = Date.now();
        currentQuestionIndex = 0;
        userAnswers = [];
        
        if (currentQuiz.questions && currentQuiz.questions.length > 0) {
            displayQuestion(currentQuiz.questions[0], 0, currentQuiz.questions.length);
        } else {
            alert('Kviz nema pitanja!');
            window.location.href = 'my-quizzes.html';
        }
    } catch (error) {
        console.error('🟣 QUIZ-TAKE.JS - Error initializing quiz:', error);
        alert('Greška pri učitavanju kviza: ' + error.message);
        window.location.href = 'my-quizzes.html';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('🟣 QUIZ-TAKE.JS - DOMContentLoaded pozvan');
    
    // Back to quizzes button
    const backBtn = document.getElementById('backToQuizzesBtn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            window.location.href = 'my-quizzes.html';
        });
    }
    
    // View all results button
    const viewAllResultsBtn = document.getElementById('viewAllResultsBtn');
    if (viewAllResultsBtn) {
        viewAllResultsBtn.addEventListener('click', () => {
            const quizId = getQuizIdFromURL();
            window.location.href = `quiz-results.html?quiz_id=${quizId}`;
        });
    }
    
    // Initialize quiz
    initQuiz();
});

