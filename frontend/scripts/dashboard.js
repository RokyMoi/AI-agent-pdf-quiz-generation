// Dashboard JavaScript
// ====================
// checkAuth i getUserData su već definisani u common.js

// Load user stats
async function loadUserStats() {
    console.log('🟢 DASHBOARD.JS - loadUserStats() pozvan');
    
    const user = getUserData();
    if (!user) {
        console.error('🟢 DASHBOARD.JS - Nema userData');
        return;
    }
    
    // Update username display
    const usernameElements = document.querySelectorAll('#usernameDisplay, #userName');
    usernameElements.forEach(el => {
        if (el) el.textContent = user.username || 'Korisnik';
    });
    
    // Load fresh stats from API
    try {
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/user/stats?user_id=${user.id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            console.log('🟢 DASHBOARD.JS - Stats from API:', stats);
            
            document.getElementById('totalQuizzes').textContent = stats.total_quizzes || 0;
            document.getElementById('totalScore').textContent = stats.total_score || 0;
            document.getElementById('avgAccuracy').textContent = 
                stats.average_accuracy ? (stats.average_accuracy * 100).toFixed(1) + '%' : '0%';
            
            // Update localStorage with fresh data
            user.total_quizzes = stats.total_quizzes || 0;
            user.total_score = stats.total_score || 0;
            user.average_accuracy = stats.average_accuracy || 0;
            localStorage.setItem('userData', JSON.stringify(user));
        } else {
            // Fallback to localStorage data
            console.warn('🟢 DASHBOARD.JS - API call failed, using localStorage data');
            document.getElementById('totalQuizzes').textContent = user.total_quizzes || 0;
            document.getElementById('totalScore').textContent = user.total_score || 0;
            document.getElementById('avgAccuracy').textContent = 
                user.average_accuracy ? (user.average_accuracy * 100).toFixed(1) + '%' : '0%';
        }
    } catch (error) {
        console.error('🟢 DASHBOARD.JS - Error loading stats:', error);
        // Fallback to localStorage data
        document.getElementById('totalQuizzes').textContent = user.total_quizzes || 0;
        document.getElementById('totalScore').textContent = user.total_score || 0;
        document.getElementById('avgAccuracy').textContent = 
            user.average_accuracy ? (user.average_accuracy * 100).toFixed(1) + '%' : '0%';
    }
}

// Load recent activity
function loadRecentActivity() {
    const activityContainer = document.getElementById('recentActivity');
    if (!activityContainer) return;
    
    // Placeholder - in production, fetch from API
    activityContainer.innerHTML = '<p class="no-activity">Nema nedavne aktivnosti</p>';
}

// handleLogout je već definisan u common.js

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // checkAuth je iz common.js
    if (typeof checkAuth === 'function') {
        if (!checkAuth()) return;
    } else {
        console.error('checkAuth nije dostupan iz common.js!');
        return;
    }
    
    loadUserStats();
    loadRecentActivity();
    
    // handleLogout je iz common.js, ali možemo dodati dodatni event listener ako treba
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn && typeof handleLogout !== 'function') {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('userData');
            localStorage.removeItem('userId');
            window.location.href = "../pages/login.html";
        });
    }
});

