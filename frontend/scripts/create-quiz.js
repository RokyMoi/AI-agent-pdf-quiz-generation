// Create Quiz JavaScript
// ======================
// checkAuth je već definisan u common.js

// File upload handling
function setupFileUpload() {
    const fileInput = document.getElementById('pdfFile');
    const uploadArea = document.getElementById('fileUploadArea');
    const fileInfo = document.getElementById('fileInfo');
    
    if (!fileInput || !uploadArea) return;
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#7C3AED';
        uploadArea.style.background = 'rgba(139, 92, 246, 0.1)';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#8B5CF6';
        uploadArea.style.background = '#FAFAFA';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#8B5CF6';
        uploadArea.style.background = '#FAFAFA';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    const fileInfo = document.getElementById('fileInfo');
    if (!fileInfo) return;
    
    if (file.type !== 'application/pdf') {
        fileInfo.innerHTML = '<span style="color: #EF4444;">❌ Molimo izaberite PDF fajl</span>';
        fileInfo.style.display = 'block';
        return;
    }
    
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    fileInfo.innerHTML = `
        <strong>📄 ${file.name}</strong><br>
        <small>Veličina: ${fileSize} MB</small>
    `;
    fileInfo.style.display = 'block';
}

// Handle form submission
function handleFormSubmit(event) {
    event.preventDefault();
    
    // Validate form
    const quizTitle = document.getElementById('quizTitle').value;
    const pdfFile = document.getElementById('pdfFile').files[0];
    const numQuestions = document.getElementById('numQuestions').value;
    const chunkSize = document.getElementById('chunkSize').value;
    const topicKeywords = document.getElementById('topicKeywords').value;
    
    if (!quizTitle || !quizTitle.trim()) {
        showError('Unesite naslov kviza');
        return;
    }
    
    if (!pdfFile) {
        showError('Izaberite PDF fajl');
        return;
    }
    
    // Store quiz data in sessionStorage
    const quizData = {
        quizTitle: quizTitle,
        numQuestions: parseInt(numQuestions),
        chunkSize: parseInt(chunkSize),
        topicKeywords: topicKeywords,
        pdfFileName: pdfFile.name,
        pdfFileSize: pdfFile.size
    };
    
    // Store file in sessionStorage as base64
    const reader = new FileReader();
    reader.onload = function(e) {
        sessionStorage.setItem('quizData', JSON.stringify(quizData));
        sessionStorage.setItem('pdfFileData', e.target.result);
        sessionStorage.setItem('pdfFileName', pdfFile.name);
        
        // Redirect to loading page
        window.location.href = 'loading.html';
    };
    reader.onerror = function() {
        showError('Greška pri učitavanju PDF fajla');
    };
    reader.readAsDataURL(pdfFile);
}

// Simulate quiz creation with progress
function simulateQuizCreation() {
    let progress = 0;
    
    // Step 1: Parsing PDF (0-25%)
    activateStep('step1');
    updateProgress(5, 'Učitavanje PDF fajla...');
    
    setTimeout(() => {
        updateProgress(15, 'Parsiranje PDF dokumenta...');
        setTimeout(() => {
            completeStep('step1');
            updateProgress(25, 'PDF uspešno parsiran');
            
            // Step 2: Chunking (25-50%)
            activateStep('step2');
            updateProgress(30, 'Segmentacija teksta...');
            
            setTimeout(() => {
                updateProgress(40, 'Kreiranje chunk-ova...');
                setTimeout(() => {
                    completeStep('step2');
                    updateProgress(50, 'Segmentacija završena');
                    
                    // Step 3: Generating questions (50-85%)
                    activateStep('step3');
                    updateProgress(55, 'Generisanje pitanja sa AI...');
                    
                    let questionProgress = 55;
                    const questionInterval = setInterval(() => {
                        questionProgress += 3;
                        if (questionProgress <= 85) {
                            updateProgress(questionProgress, `Generisanje pitanja... ${Math.floor((questionProgress - 55) / 30 * 100)}%`);
                        } else {
                            clearInterval(questionInterval);
                            completeStep('step3');
                            updateProgress(85, 'Pitanja generisana');
                            
                            // Step 4: Finalizing (85-100%)
                            activateStep('step4');
                            updateProgress(90, 'Priprema kviza...');
                            
                            setTimeout(() => {
                                updateProgress(95, 'Finalizacija...');
                                setTimeout(() => {
                                    completeStep('step4');
                                    updateProgress(100, 'Kviz je spreman!');
                                    
                                    // Hide loading screen after a moment
                                    setTimeout(() => {
                                        document.getElementById('loadingScreen').style.display = 'none';
                                        
                                        // Show quiz area and action buttons
                                        document.getElementById('quizArea').style.display = 'block';
                                        document.getElementById('quizActions').style.display = 'flex';
                                        
                                        // Show success message
                                        const statusMessage = document.getElementById('statusMessage');
                                        statusMessage.textContent = '✅ PDF uspešno učitan! Kviz je spreman. Možete pregledati ili sačuvati kviz.';
                                        statusMessage.className = 'status-message success';
                                        statusMessage.style.display = 'block';
                                        
                                        // Load first question
                                        loadQuestion();
                                    }, 500);
                                }, 500);
                            }, 500);
                        }
                    }, 200);
                }, 1000);
            }, 1000);
        }, 1000);
    }, 1000);
}

// Update progress bar
function updateProgress(percent, status) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    
    if (progressBar) {
        progressBar.style.width = percent + '%';
    }
    if (progressPercent) {
        progressPercent.textContent = Math.round(percent) + '%';
    }
    if (progressStatus) {
        progressStatus.textContent = status;
    }
}

// Reset all steps
function resetSteps() {
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`step${i}`);
        if (step) {
            step.classList.remove('active', 'completed');
            const icon = step.querySelector('.step-icon');
            if (icon) {
                icon.textContent = '⏳';
            }
        }
    }
}

// Activate a step
function activateStep(stepId) {
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.add('active');
        step.classList.remove('completed');
        const icon = step.querySelector('.step-icon');
        if (icon) {
            icon.textContent = '⏳';
        }
    }
}

// Complete a step
function completeStep(stepId) {
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.remove('active');
        step.classList.add('completed');
        const icon = step.querySelector('.step-icon');
        if (icon) {
            icon.textContent = '✅';
        }
    }
}

// Load question
function loadQuestion() {
    // Placeholder - in production, fetch from API
    const questionText = document.getElementById('questionText');
    const currentQuestionTitle = document.getElementById('currentQuestionTitle');
    
    if (questionText) {
        questionText.innerHTML = `
            <h3>Primer Pitanje:</h3>
            <p>Koja je glavna prednost korišćenja machine learning algoritama?</p>
        `;
    }
    
    if (currentQuestionTitle) {
        currentQuestionTitle.textContent = 'Pitanje 1 od 10';
    }
    
    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = '10%';
    }
    
    // Set option texts (placeholder)
    const optionA = document.getElementById('optionA');
    const optionB = document.getElementById('optionB');
    const optionC = document.getElementById('optionC');
    const optionD = document.getElementById('optionD');
    
    if (optionA) {
        const text = optionA.querySelector('.option-text');
        if (text) text.textContent = 'Brže izvršavanje';
    }
    if (optionB) {
        const text = optionB.querySelector('.option-text');
        if (text) text.textContent = 'Automatsko učenje iz podataka';
    }
    if (optionC) {
        const text = optionC.querySelector('.option-text');
        if (text) text.textContent = 'Manje memorije';
    }
    if (optionD) {
        const text = optionD.querySelector('.option-text');
        if (text) text.textContent = 'Jednostavnija implementacija';
    }
}

// Handle option click
function handleOptionClick(option) {
    const resultDisplay = document.getElementById('resultDisplay');
    const explanationDisplay = document.getElementById('explanationDisplay');
    const nextBtn = document.getElementById('nextQuestionBtn');
    const progressFill = document.getElementById('progressFill');
    
    // Disable all option buttons
    ['A', 'B', 'C', 'D'].forEach(opt => {
        const btn = document.getElementById(`option${opt}`);
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.6';
        }
    });
    
    // Highlight selected option
    const selectedBtn = document.getElementById(`option${option}`);
    if (selectedBtn) {
        selectedBtn.style.background = 'rgba(139, 92, 246, 0.2)';
    }
    
    // Simulate answer (in production, this would be real)
    const isCorrect = Math.random() > 0.5; // Random for demo
    
    if (isCorrect) {
        resultDisplay.innerHTML = `✅ <strong>Tačno!</strong> Vaš odgovor: ${option}`;
        resultDisplay.style.background = 'rgba(16, 185, 129, 0.1)';
        resultDisplay.style.borderLeftColor = '#10B981';
    } else {
        resultDisplay.innerHTML = `❌ <strong>Netačno.</strong> Vaš odgovor: ${option}, Tačan odgovor: B`;
        resultDisplay.style.background = 'rgba(239, 68, 68, 0.1)';
        resultDisplay.style.borderLeftColor = '#EF4444';
    }
    resultDisplay.style.display = 'block';
    
    explanationDisplay.innerHTML = `
        <p><strong>Objašnjenje:</strong></p>
        <p>Machine learning algoritmi omogućavaju sistemima da automatski uče i poboljšavaju se iz podataka bez eksplicitnog programiranja za svaki zadatak.</p>
    `;
    explanationDisplay.style.display = 'block';
    
    nextBtn.style.display = 'block';
    
    // Update progress
    if (progressFill) {
        const currentWidth = parseInt(progressFill.style.width) || 10;
        const newWidth = Math.min(currentWidth + 10, 100);
        progressFill.style.width = newWidth + '%';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    if (!checkAuth()) return;
    
    setupFileUpload();
    
    const form = document.getElementById('createQuizForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // Option buttons
    ['A', 'B', 'C', 'D'].forEach(option => {
        const btn = document.getElementById(`option${option}`);
        if (btn) {
            btn.addEventListener('click', () => handleOptionClick(option));
        }
    });
    
    // Next question button
    const nextBtn = document.getElementById('nextQuestionBtn');
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            // Reset option buttons
            ['A', 'B', 'C', 'D'].forEach(opt => {
                const btn = document.getElementById(`option${opt}`);
                if (btn) {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.style.background = '';
                }
            });
            
            // Hide result and explanation
            document.getElementById('resultDisplay').style.display = 'none';
            document.getElementById('explanationDisplay').style.display = 'none';
            nextBtn.style.display = 'none';
            
            // Load next question
            loadQuestion();
        });
    }
    
    // Preview button
    const previewBtn = document.getElementById('previewBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', () => {
            alert('Preview funkcionalnost će prikazati pregled kviza pre objavljivanja.');
        });
    }
    
    // Save button
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const quizTitle = document.getElementById('quizTitle').value;
            if (quizTitle) {
                alert(`Kviz "${quizTitle}" je sačuvan!`);
            } else {
                alert('Unesite naslov kviza pre čuvanja.');
            }
        });
    }
});

