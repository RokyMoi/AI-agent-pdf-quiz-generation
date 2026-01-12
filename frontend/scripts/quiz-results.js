// Quiz Results JavaScript
// =======================
// API_BASE_URL is already defined in common.js

console.log('🟡 QUIZ-RESULTS.JS SE UČITAVA!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🟡 QUIZ-RESULTS.JS - DOMContentLoaded pozvan');
    
    if (typeof checkAuth === 'function') {
        if (!checkAuth()) return;
    }
    
    // Check if quiz_id is in URL (from my-quizzes page)
    const params = new URLSearchParams(window.location.search);
    const quizId = params.get('quiz_id');
    
    if (quizId) {
        // Load results directly for this quiz
        loadQuizResults(quizId);
    } else {
        // Load quiz selector
        loadQuizzes();
    }
    
    const quizSelect = document.getElementById('quizSelect');
    if (quizSelect) {
        quizSelect.addEventListener('change', handleQuizChange);
    }
});

async function loadQuizzes() {
    console.log('🟡 QUIZ-RESULTS.JS - loadQuizzes() pozvan');
    
    try {
        const userData = getUserData();
        if (!userData || !userData.id) {
            console.error('🟡 QUIZ-RESULTS.JS - Nema userData');
            return;
        }
        
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/my_quizzes?user_id=${userData.id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Greška pri učitavanju kvizova');
        }
        
        const quizzes = await response.json();
        const quizSelect = document.getElementById('quizSelect');
        
        if (quizSelect && quizzes.length > 0) {
            quizSelect.innerHTML = '<option value="">Izaberite kviz...</option>';
            quizzes.forEach(quiz => {
                const option = document.createElement('option');
                option.value = quiz.id;
                option.textContent = quiz.title || `Kviz #${quiz.id}`;
                quizSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading quizzes:', error);
    }
}

async function handleQuizChange(e) {
    const quizId = e.target.value;
    if (!quizId) {
        document.getElementById('dashboardStats').style.display = 'none';
        document.getElementById('resultsBody').innerHTML = '<tr><td colspan="7" class="loading">Izaberite kviz...</td></tr>';
        return;
    }
    
    await loadQuizResults(quizId);
}

async function loadQuizResults(quizId) {
    console.log('🟡 QUIZ-RESULTS.JS - loadQuizResults() pozvan za quiz ID:', quizId);
    
    try {
        const userData = getUserData();
        if (!userData || !userData.id) {
            console.error('🟡 QUIZ-RESULTS.JS - Nema userData');
            return;
        }
        
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/quiz_results/${quizId}?user_id=${userData.id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Greška pri učitavanju rezultata');
        }
        
        const data = await response.json();
        console.log('🟡 QUIZ-RESULTS.JS - Primljeni podaci:', data);
        console.log('🟡 QUIZ-RESULTS.JS - Stats:', data.stats);
        console.log('🟡 QUIZ-RESULTS.JS - Results:', data.results);
        console.log('🟡 QUIZ-RESULTS.JS - Results length:', data.results ? data.results.length : 0);
        
        // Update dashboard stats
        if (data.stats) {
            updateDashboardStats(data.stats);
        }
        
        // Update results table
        if (data.results) {
            updateResultsTable(data.results);
        } else {
            console.warn('🟡 QUIZ-RESULTS.JS - Nema results u odgovoru!');
            const tbody = document.getElementById('resultsBody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="7" class="loading">Nema rezultata za ovaj kviz</td></tr>';
            }
        }
        
        // Update IP analysis
        if (data.ip_analysis) {
            updateIPAnalysis(data.ip_analysis);
        }
        
        const dashboardStats = document.getElementById('dashboardStats');
        if (dashboardStats) dashboardStats.style.display = 'grid';
        
    } catch (error) {
        console.error('🟡 QUIZ-RESULTS.JS - Error loading results:', error);
        const resultsBody = document.getElementById('resultsBody');
        if (resultsBody) {
            resultsBody.innerHTML = `<tr><td colspan="7" style="color: #ff0000;">Greška: ${error.message}</td></tr>`;
        }
    }
}

function updateDashboardStats(stats) {
    if (!stats) return;
    
    const totalUsers = document.getElementById('totalUsers');
    const totalAttempts = document.getElementById('totalAttempts');
    const avgScore = document.getElementById('avgScore');
    const avgAccuracy = document.getElementById('avgAccuracy');
    
    if (totalUsers) totalUsers.textContent = stats.total_users || 0;
    if (totalAttempts) totalAttempts.textContent = stats.total_attempts || 0;
    if (avgScore) avgScore.textContent = (stats.avg_score || 0) + '%';
    if (avgAccuracy) avgAccuracy.textContent = (stats.avg_accuracy || 0) + '%';
}

function updateResultsTable(results) {
    const tbody = document.getElementById('resultsBody');
    if (!tbody) return;
    
    if (!results || results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Nema rezultata za ovaj kviz</td></tr>';
        return;
    }
    
    tbody.innerHTML = results.map(result => `
        <tr>
            <td>${result.username || 'N/A'}</td>
            <td>${result.email || 'N/A'}</td>
            <td>${result.score || 0}/${result.total_questions || 0}</td>
            <td>${(result.accuracy || 0).toFixed(1)}%</td>
            <td>${result.completed_at ? (new Date(result.completed_at).toLocaleDateString('sr-RS') || result.completed_at) : 'N/A'}</td>
            <td>${result.ip_address || 'N/A'}</td>
            <td>
                <button class="btn-small btn-view" onclick="viewDetails(${result.id})">
                    Detalji
                </button>
            </td>
        </tr>
    `).join('');
}

function updateIPAnalysis(ipAnalysis) {
    const ipAnalysisDiv = document.getElementById('ipAnalysis');
    if (!ipAnalysisDiv) return;
    
    if (!ipAnalysis || Object.keys(ipAnalysis).length === 0) {
        ipAnalysisDiv.innerHTML = '<p>Nema podataka za analizu IP adresa</p>';
        return;
    }
    
    let html = '<div class="ip-analysis-grid">';
    
    // Show suspicious IPs (multiple users from same IP)
    const suspiciousIPs = Object.entries(ipAnalysis)
        .filter(([ip, data]) => data.user_count > 1)
        .map(([ip, data]) => ({
            ip,
            user_count: data.user_count,
            users: data.users,
            attempts: data.attempt_count
        }));
    
    if (suspiciousIPs.length > 0) {
        html += '<div class="suspicious-ips">';
        html += '<h3 style="color: #ff0000; margin-bottom: 1rem;">⚠️ Sumnjive IP Adrese</h3>';
        suspiciousIPs.forEach(item => {
            html += `
                <div class="ip-item" style="padding: 1rem; background: #2F2F2F; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #ff0000;">
                    <strong>IP:</strong> ${item.ip}<br>
                    <strong>Korisnika:</strong> ${item.user_count}<br>
                    <strong>Pokušaja:</strong> ${item.attempts}<br>
                    <strong>Korisnici:</strong> ${item.users.join(', ')}
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Show all IPs
    html += '<div class="all-ips">';
    html += '<h3 style="margin-bottom: 1rem;">Sve IP Adrese</h3>';
    Object.entries(ipAnalysis).forEach(([ip, data]) => {
        html += `
            <div class="ip-item" style="padding: 0.75rem; background: #1a1a1a; border-radius: 4px; margin-bottom: 0.5rem;">
                <strong>${ip}</strong> - ${data.user_count} korisnik(a), ${data.attempt_count} pokušaj(a)
            </div>
        `;
    });
    html += '</div>';
    
    html += '</div>';
    ipAnalysisDiv.innerHTML = html;
}

function viewDetails(resultId) {
    // TODO: Open modal or navigate to detailed result page
    alert(`Detalji rezultata #${resultId} (funkcionalnost u izradi)`);
}

// Eksportuj funkciju na window objekat
window.viewDetails = viewDetails;
