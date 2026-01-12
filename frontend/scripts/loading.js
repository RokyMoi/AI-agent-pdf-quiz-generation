// Loading Screen JavaScript with API Integration
// =============================================

console.log('🟢 LOADING.JS - Script se učitava...');

// API_BASE_URL should be defined in common.js (which is loaded before this script)
// Don't redeclare it, just use it
if (typeof API_BASE_URL === 'undefined') {
    console.error('🟢 LOADING.JS - API_BASE_URL nije definisan! Proverite da li je common.js učitan pre loading.js');
} else {
    console.log('🟢 LOADING.JS - API_BASE_URL iz common.js:', API_BASE_URL);
}

// Get quiz data from sessionStorage (passed from create-quiz page)
function getQuizData() {
    const data = sessionStorage.getItem('quizData');
    const pdfFileData = sessionStorage.getItem('pdfFileData');
    const pdfFileName = sessionStorage.getItem('pdfFileName');
    
    if (!data) return null;
    
    const quizData = JSON.parse(data);
    
    // Convert base64 back to File object for FormData
    if (pdfFileData && pdfFileName) {
        try {
            // Extract base64 data and mime type
            const base64Data = pdfFileData.split(',')[1];
            const mimeString = pdfFileData.split(',')[0].split(':')[1].split(';')[0];
            
            // Convert base64 to binary
            const byteCharacters = atob(base64Data);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: mimeString });
            
            // Create File object
            quizData.pdfFile = new File([blob], pdfFileName, { type: mimeString });
        } catch (error) {
            console.error('Error converting base64 to File:', error);
            return null;
        }
    }
    
    return quizData;
}

// Add console log message
function addConsoleLog(message, type = 'info') {
    const consoleLogs = document.getElementById('consoleLogs');
    if (!consoleLogs) {
        console.log(`[${type.toUpperCase()}] ${message}`);
        return;
    }
    
    const line = document.createElement('div');
    line.className = 'console-line';
    
    const prompt = document.createElement('span');
    prompt.className = 'console-prompt';
    prompt.textContent = '$';
    
    const timestamp = new Date().toLocaleTimeString('sr-RS', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const text = document.createElement('span');
    text.className = `console-text ${type}`;
    text.textContent = `[${timestamp}] ${message}`;
    
    line.appendChild(prompt);
    line.appendChild(text);
    consoleLogs.appendChild(line);
    
    // Auto scroll to bottom
    consoleLogs.scrollTop = consoleLogs.scrollHeight;
    
    // Also log to browser console
    console.log(`[${type.toUpperCase()}] ${message}`);
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

// Time estimates for each step (in hours)
const TIME_ESTIMATES = {
    step1: { min: 0.5, max: 2, name: 'Parsiranje PDF-a' },
    step2: { min: 0.25, max: 1, name: 'Segmentacija teksta' },
    step3: { min: 1, max: 3, name: 'Generisanje pitanja' },
    step4: { min: 0.1, max: 0.5, name: 'Finalizacija kviza' }
};

// Sleep helper function
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Reset all steps
function resetSteps() {
    console.log('🟢 LOADING.JS - resetSteps() pozvan');
    
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`step${i}`);
        if (step) {
            step.classList.remove('active', 'completed');
            step.classList.add('pending');
        } else {
            console.warn(`🟢 LOADING.JS - step${i} element nije pronađen!`);
        }
    }
    
    // Clear console
    const consoleLogs = document.getElementById('consoleLogs');
    if (consoleLogs) {
        consoleLogs.innerHTML = '';
        console.log('🟢 LOADING.JS - Console logs očišćeni');
    } else {
        console.warn('🟢 LOADING.JS - consoleLogs element nije pronađen!');
    }
    
    addConsoleLog('Sistem inicijalizovan. Počinje procesiranje PDF dokumenta...', 'info');
    console.log('🟢 LOADING.JS - resetSteps() završen');
}

// Activate a step
function activateStep(stepId) {
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.remove('pending', 'completed');
        step.classList.add('active');
        
        const estimate = TIME_ESTIMATES[stepId];
        if (estimate) {
            addConsoleLog(`Pokretanje: ${estimate.name} (procenjeno vreme: ${estimate.min}-${estimate.max} sata)`, 'info');
        }
    }
}

// Complete a step
function completeStep(stepId) {
    const step = document.getElementById(stepId);
    if (step) {
        step.classList.remove('active', 'pending');
        step.classList.add('completed');
        
        const estimate = TIME_ESTIMATES[stepId];
        if (estimate) {
            addConsoleLog(`${estimate.name} završeno uspešno.`, 'success');
        }
    }
}

// Show error
function showError(message) {
    const errorDisplay = document.getElementById('errorDisplay');
    const errorMessage = document.getElementById('errorMessage');
    const loadingSteps = document.querySelector('.loading-steps');
    
    if (errorDisplay && errorMessage) {
        errorMessage.textContent = message;
        errorDisplay.style.display = 'block';
        if (loadingSteps) {
            loadingSteps.style.display = 'none';
        }
    }
}

// Hide error
function hideError() {
    const errorDisplay = document.getElementById('errorDisplay');
    const loadingSteps = document.querySelector('.loading-steps');
    
    if (errorDisplay) {
        errorDisplay.style.display = 'none';
    }
    if (loadingSteps) {
        loadingSteps.style.display = 'flex';
    }
}

// Check API health and key
async function checkAPIHealth() {
    console.log('🟢 LOADING.JS - checkAPIHealth() pozvan');
    console.log('🟢 LOADING.JS - API_BASE_URL:', API_BASE_URL);
    
    try {
        addConsoleLog('Povezivanje sa API serverom...', 'info');
        console.log('🟢 LOADING.JS - Šaljem fetch zahtev na:', `${API_BASE_URL}/api/health`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 sekundi timeout
        
        let response;
        try {
            response = await fetch(`${API_BASE_URL}/api/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (fetchError) {
            clearTimeout(timeoutId);
            console.error('🟢 LOADING.JS - Fetch error:', fetchError);
            if (fetchError.name === 'AbortError') {
                throw new Error('Zahtev je prekoračio vreme čekanja (10 sekundi). Proverite da li je backend server pokrenut.');
            }
            throw fetchError;
        }
        
        console.log('🟢 LOADING.JS - Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('🟢 LOADING.JS - Response not OK:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('🟢 LOADING.JS - Health check data:', data);
        addConsoleLog('✓ API server je dostupan', 'success');
        
        if (!data.api_key_valid) {
            addConsoleLog('⚠️ Upozorenje: Google API key nije validan', 'warning');
            // Don't throw error, just warn - let it continue
        } else {
            addConsoleLog('✓ Google API key je validan', 'success');
        }
        
        return true;
    } catch (error) {
        console.error('🟢 LOADING.JS - Error in checkAPIHealth:', error);
        addConsoleLog(`✗ Greška pri povezivanju sa API serverom: ${error.message}`, 'error');
        addConsoleLog(`Proverite da li je backend server pokrenut na ${API_BASE_URL}`, 'error');
        throw new Error(`API server nije dostupan: ${error.message}`);
    }
}

// Call API to create quiz
async function createQuizAPI(quizData) {
    console.log('🟢 LOADING.JS - createQuizAPI() pozvan sa:', quizData);
    addConsoleLog('Inicijalizacija procesa kreiranja kviza...', 'info');
    
    try {
        // Check API health first
        updateProgress(5, 'Provera API konekcije...');
        addConsoleLog('Povezivanje sa API serverom...', 'info');
        console.log('🟢 LOADING.JS - Pozivam checkAPIHealth()...');
        
        await checkAPIHealth();
        
        console.log('🟢 LOADING.JS - checkAPIHealth() završen uspešno');
        addConsoleLog('API konekcija uspešna. Nastavljam sa parsiranjem PDF-a...', 'info');
        
        // Step 1: Parse PDF (0-25%)
        activateStep('step1');
        updateProgress(5, 'Učitavanje PDF fajla...');
        addConsoleLog('Učitavanje PDF fajla...', 'info');
        
        if (!quizData.pdfFile) {
            throw new Error('PDF fajl nije učitan. Molimo pokušajte ponovo.');
        }
        
        const formData = new FormData();
        formData.append('pdf_file', quizData.pdfFile);
        formData.append('quiz_title', quizData.quizTitle);
        formData.append('num_questions', quizData.numQuestions);
        formData.append('chunk_size', quizData.chunkSize);
        formData.append('topic_keywords', quizData.topicKeywords || '');
        
        updateProgress(15, 'Parsiranje PDF dokumenta...');
        addConsoleLog('Slanje PDF fajla na server za parsiranje...', 'info');
        addConsoleLog(`PDF fajl: ${quizData.pdfFile.name} (${(quizData.pdfFile.size / 1024 / 1024).toFixed(2)} MB)`, 'info');
        addConsoleLog(`API endpoint: ${API_BASE_URL}/api/upload_pdf`, 'info');
        
        let response;
        try {
            response = await fetch(`${API_BASE_URL}/api/upload_pdf`, {
                method: 'POST',
                body: formData
            });
        } catch (fetchError) {
            addConsoleLog(`✗ Greška pri povezivanju sa serverom: ${fetchError.message}`, 'error');
            addConsoleLog(`Proverite da li je backend server pokrenut na ${API_BASE_URL}`, 'error');
            addConsoleLog(`Tip greške: ${fetchError.name}`, 'error');
            throw new Error(`Ne mogu da se povežem sa serverom: ${fetchError.message}. Proverite da li je backend server pokrenut.`);
        }
        
        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: `HTTP error! status: ${response.status} ${response.statusText}` };
            }
            const errorMsg = errorData.error || `HTTP error! status: ${response.status}`;
            addConsoleLog(`✗ Greška pri parsiranju PDF-a: ${errorMsg}`, 'error');
            addConsoleLog(`HTTP status: ${response.status} ${response.statusText}`, 'error');
            throw new Error(errorMsg);
        }
        
        // Read streaming response (Server-Sent Events)
        let result = null;
        let parseError = null;
        
        try {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            addConsoleLog('✓ Povezan sa serverom. Čekam progres parsiranja...', 'success');
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    break;
                }
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.type === 'progress') {
                                // Update progress based on page parsing
                                if (data.current_page !== undefined && data.total_pages !== undefined) {
                                    const pageProgress = 15 + (data.current_page / data.total_pages) * 10; // 15-25% for parsing
                                    updateProgress(Math.min(pageProgress, 25), `Parsiranje stranice ${data.current_page}/${data.total_pages}...`);
                                    addConsoleLog(`📄 ${data.status}`, 'info');
                                } else if (data.stage === 'chunking') {
                                    // Chunking progress with detailed updates
                                    if (data.current_chunk !== undefined && data.total_chunks !== undefined) {
                                        const chunkProgress = 25 + (data.current_chunk / data.total_chunks) * 10; // 25-35% for chunking
                                        updateProgress(Math.min(chunkProgress, 35), `Segmentacija: ${data.current_chunk}/${data.total_chunks} segmenata...`);
                                        addConsoleLog(`✂️ ${data.status}`, 'info');
                                    } else {
                                        updateProgress(25, 'Segmentacija teksta...');
                                        addConsoleLog(`✂️ ${data.status}`, 'info');
                                    }
                                } else if (data.stage === 'filtering') {
                                    // Filtering progress with detailed updates
                                    if (data.current_chunk !== undefined && data.total_chunks !== undefined) {
                                        const filterProgress = 35 + (data.current_chunk / data.total_chunks) * 5; // 35-40% for filtering
                                        updateProgress(Math.min(filterProgress, 40), `Filtriranje: ${data.current_chunk}/${data.total_chunks}...`);
                                        addConsoleLog(`🔍 ${data.status}`, 'info');
                                    } else {
                                        updateProgress(35, 'Filtriranje segmenata...');
                                        addConsoleLog(`🔍 ${data.status}`, 'info');
                                    }
                                } else {
                                    addConsoleLog(`ℹ️ ${data.status}`, 'info');
                                }
                            } else if (data.type === 'complete') {
                                result = data;
                                addConsoleLog(`✓ ${data.message}`, 'success');
                                if (data.num_chunks) {
                                    addConsoleLog(`📊 Ukupno segmenata: ${data.num_chunks}`, 'info');
                                }
                                break;
                            } else if (data.type === 'error') {
                                parseError = new Error(data.message);
                                addConsoleLog(`✗ Greška: ${data.message}`, 'error');
                                break;
                            } else if (data.type === 'heartbeat') {
                                // Keep connection alive, no action needed
                            }
                        } catch (e) {
                            // Skip invalid JSON lines
                            console.warn('Invalid JSON in SSE stream:', line);
                        }
                    }
                }
                
                if (result || parseError) {
                    break;
                }
            }
            
            if (parseError) {
                throw parseError;
            }
            
            if (!result) {
                throw new Error('Nije primljen kompletan odgovor sa servera.');
            }
            
        } catch (streamError) {
            addConsoleLog(`✗ Greška pri čitanju stream-a: ${streamError.message}`, 'error');
            throw streamError;
        }
        
        if (result.error) {
            addConsoleLog(`✗ Greška: ${result.error}`, 'error');
            throw new Error(result.error);
        }
        
        if (!result.success) {
            const errorMsg = result.message || 'Greška pri parsiranju PDF-a';
            addConsoleLog(`✗ Greška: ${errorMsg}`, 'error');
            throw new Error(errorMsg);
        }
        completeStep('step1');
        updateProgress(25, 'PDF uspešno parsiran');
        
        // Step 2: Chunking (25-50%)
        activateStep('step2');
        updateProgress(30, 'Segmentacija teksta...');
        addConsoleLog('Pokretanje segmentacije teksta...', 'info');
        
        // Get chunks from result
        const chunks = result.chunks || [];
        if (chunks.length > 0) {
            addConsoleLog(`✓ Segmentacija završena. Kreirano ${chunks.length} segmenta`, 'success');
        } else {
            addConsoleLog('⚠️ Nema segmenta za obradu', 'warning');
        }
        
        // Simulate chunking progress (in real API, this would be streamed)
        await new Promise(resolve => setTimeout(resolve, 500));
        updateProgress(40, 'Kreiranje chunk-ova...');
        addConsoleLog('Priprema segmenta za generisanje pitanja...', 'info');
        await new Promise(resolve => setTimeout(resolve, 500));
        
        completeStep('step2');
        updateProgress(50, 'Segmentacija završena');
        
        // Step 3: Generate questions one by one (50-90%) - LIKE QUICK QUIZ!
        activateStep('step3');
        updateProgress(50, 'Povezivanje sa Gemini API...');
        addConsoleLog('Povezivanje sa Gemini API za generisanje pitanja...', 'info');
        await sleep(500);
        
        addConsoleLog('✓ Povezano sa Gemini API', 'success');
        addConsoleLog(`Generišem ${quizData.numQuestions} pitanja iz ${chunks.length} segmenata...`, 'info');
        await sleep(500);
        
        const generatedQuestions = [];
        let chunkIndex = 0;
        
        // Generate questions one by one (like quick quiz)
        for (let i = 0; i < quizData.numQuestions; i++) {
            const questionNum = i + 1;
            const progress = 50 + ((i + 1) / quizData.numQuestions) * 40; // 50-90%
            
            addConsoleLog(`Generišem pitanje ${questionNum}/${quizData.numQuestions}...`, 'info');
            updateProgress(Math.floor(progress), `Generisanje pitanja ${questionNum}...`);
            
            // Select chunk (round-robin or random)
            const selectedChunk = chunks[chunkIndex % chunks.length];
            chunkIndex++;
            
            try {
                // Add timeout for fetch (90 seconds)
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 90000);
                
                let questionResponse;
                try {
                    questionResponse = await fetch(`${API_BASE_URL}/api/generate_question_from_chunk`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            chunk: selectedChunk,
                            question_number: questionNum,
                            difficulty: 'medium'
                        }),
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);
                } catch (fetchError) {
                    clearTimeout(timeoutId);
                    if (fetchError.name === 'AbortError') {
                        throw new Error('Zahtev je prekoračio vreme čekanja (90 sekundi). Proverite API server.');
                    }
                    throw new Error(`Greška pri povezivanju sa serverom: ${fetchError.message}`);
                }
                
                if (!questionResponse.ok) {
                    let errorData;
                    try {
                        errorData = await questionResponse.json();
                    } catch (e) {
                        errorData = { error: `HTTP ${questionResponse.status}: ${questionResponse.statusText}` };
                    }
                    
                    const errorMsg = errorData.error || `HTTP ${questionResponse.status}: ${questionResponse.statusText}`;
                    
                    // Check for specific error types
                    if (questionResponse.status === 400 && errorMsg.includes('API key')) {
                        throw new Error('API key greška. Proverite GOOGLE_API_KEY u .env fajlu.');
                    } else if (questionResponse.status === 429) {
                        throw new Error('Rate limit prekoračen. Sačekajte malo i pokušajte ponovo.');
                    } else if (questionResponse.status === 404) {
                        throw new Error('Model nije dostupan. Proverite da li vaš API key ima pristup Gemini modelima.');
                    } else {
                        throw new Error(errorMsg);
                    }
                }
                
                const question = await questionResponse.json();
                
                // Validate question structure
                if (!question || !question.question || !question.options) {
                    throw new Error('Neispravan format pitanja od API-ja');
                }
                
                generatedQuestions.push(question);
                addConsoleLog(`✓ Pitanje ${questionNum} uspešno generisano`, 'success');
                await sleep(800);
                
            } catch (error) {
                const errorMsg = error.message || 'Nepoznata greška';
                addConsoleLog(`✗ Greška pri generisanju pitanja ${questionNum}: ${errorMsg}`, 'error');
                
                // If it's an API key or model availability error, stop generation
                if (errorMsg.includes('API key') || errorMsg.includes('Model nije dostupan') || errorMsg.includes('404')) {
                    addConsoleLog('⚠️ Zaustavljam generisanje zbog API greške. Proverite API key i dostupnost modela.', 'error');
                    throw error;
                }
                
                await sleep(1000); // Wait longer on error
            }
        }
        
        if (generatedQuestions.length === 0) {
            throw new Error('Nije moguće generisati nijedno pitanje. Proverite PDF sadržaj i API konekciju.');
        }
        
        addConsoleLog(`✓ Sva pitanja uspešno generisana! (${generatedQuestions.length}/${quizData.numQuestions})`, 'success');
        completeStep('step3');
        updateProgress(90, 'Pitanja generisana');
        
        // Step 4: Finalize (90-100%)
        activateStep('step4');
        updateProgress(95, 'Priprema kviza...');
        await sleep(500);
        updateProgress(100, 'Kviz je spreman!');
        completeStep('step4');
        
        // Store quiz data for preview (matching quiz-preview.js expected format)
        const quizDataForPreview = {
            title: quizData.quizTitle,
            questions: generatedQuestions,
            topic: quizData.topicKeywords || '',
            difficulty: 'medium',
            type: 'pdf',
            chunks: result.chunks,
            numQuestions: generatedQuestions.length
        };
        
        sessionStorage.setItem('generatedQuiz', JSON.stringify(quizDataForPreview));
        
        addConsoleLog('✓ Podaci kviza sačuvani. Preusmjeravam na preview...', 'success');
        
        // Redirect to preview page
        await sleep(1000);
        window.location.href = '../pages/quiz-preview.html';
        
    } catch (error) {
        console.error('Error creating quiz:', error);
        const errorMsg = error.message || 'Greška pri kreiranju kviza. Proverite API konekciju i pokušajte ponovo.';
        addConsoleLog(`✗ KRITIČNA GREŠKA: ${errorMsg}`, 'error');
        addConsoleLog(`Tip greške: ${error.name || 'Unknown'}`, 'error');
        if (error.stack) {
            addConsoleLog(`Stack trace: ${error.stack.substring(0, 300)}...`, 'error');
        }
        addConsoleLog('Proces kreiranja kviza je zaustavljen.', 'error');
        addConsoleLog('Preporuka: Proverite da li je backend server pokrenut (python backend/api_server.py)', 'error');
        showError(errorMsg);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('🟢 LOADING.JS - DOMContentLoaded pozvan');
    
    const quizData = getQuizData();
    console.log('🟢 LOADING.JS - Quiz data:', quizData);
    
    if (quizData) {
        console.log('🟢 LOADING.JS - Quiz data pronađen, pozivam createQuizAPI()...');
        hideError();
        resetSteps();
        updateProgress(0, 'Inicijalizacija...');
        
        // Start quiz creation
        createQuizAPI(quizData).catch(error => {
            console.error('🟢 LOADING.JS - Fatal error in createQuizAPI:', error);
            addConsoleLog(`✗ Fatalna greška: ${error.message}`, 'error');
            showError(error.message || 'Greška pri kreiranju kviza');
        });
    } else {
        console.error('🟢 LOADING.JS - Nema quiz data!');
        showError('Nema podataka o kvizu. Molimo vratite se na stranicu za kreiranje kviza.');
    }
    
    // Retry button
    const retryBtn = document.getElementById('retryBtn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            console.log('🟢 LOADING.JS - Retry button kliknut');
            hideError();
            resetSteps();
            updateProgress(0, 'Inicijalizacija...');
            const quizData = getQuizData();
            if (quizData) {
                createQuizAPI(quizData).catch(error => {
                    console.error('🟢 LOADING.JS - Error on retry:', error);
                    showError(error.message || 'Greška pri kreiranju kviza');
                });
            }
        });
    }
    
    // Cancel button
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            window.location.href = '../pages/create-quiz.html';
        });
    }
});

