// Profile JavaScript
// =================

console.log('🟢 PROFILE.JS SE UČITAVA!');

// API_BASE_URL is already defined in common.js (ne deklariši ga ponovo!)
console.log('🟢 PROFILE.JS - API_BASE_URL:', typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'NEDEFINISAN');

// checkAuth je već definisan u common.js, ne treba duplikat

// Eksportuj loadProfile na window objekat da bude dostupan globalno
async function loadProfile() {
    console.log('🟢 loadProfile() pozvan');
    
    // Koristi getUserData iz common.js ako je dostupan
    let user;
    if (typeof getUserData === 'function') {
        console.log('🟢 PROFILE.JS - Koristim getUserData() iz common.js');
        user = getUserData();
    } else {
        console.warn('🟢 PROFILE.JS - getUserData() nije dostupan, koristim direktno localStorage');
        user = JSON.parse(localStorage.getItem('userData') || '{}');
    }
    
    const userId = localStorage.getItem('userId') || user?.id;
    
    console.log('🟢 User data:', user);
    console.log('🟢 User ID:', userId);
    
    // Update UI with stored data
    if (user.username) {
        console.log('🟢 Ažuriram UI sa username:', user.username);
        const usernameEl = document.getElementById('profileUsername');
        const avatarEl = document.getElementById('avatarInitial');
        const infoUsernameEl = document.getElementById('infoUsername');
        const infoEmailEl = document.getElementById('infoEmail');
        const profileEmailEl = document.getElementById('profileEmail');
        const usernameDisplayEl = document.getElementById('usernameDisplay');
        
        console.log('🟢 Pronađeni elementi:', {
            usernameEl: !!usernameEl,
            avatarEl: !!avatarEl,
            infoUsernameEl: !!infoUsernameEl,
            infoEmailEl: !!infoEmailEl,
            profileEmailEl: !!profileEmailEl,
            usernameDisplayEl: !!usernameDisplayEl
        });
        
        if (usernameEl) usernameEl.textContent = user.username;
        if (avatarEl) avatarEl.textContent = user.username[0].toUpperCase();
        if (infoUsernameEl) infoUsernameEl.textContent = user.username;
        if (infoEmailEl) infoEmailEl.textContent = user.email || 'Nije naveden';
        if (profileEmailEl) profileEmailEl.textContent = user.email || 'Nije naveden';
        if (usernameDisplayEl) usernameDisplayEl.textContent = user.username;
    } else {
        console.warn('🟢 Nema username u user data!');
    }
    
    // Load stats from API
    try {
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/user/stats?user_id=${userId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            if (stats) {
                document.getElementById('statQuizzes').textContent = stats.total_quizzes || 0;
                document.getElementById('statScore').textContent = stats.total_score || 0;
                document.getElementById('statAccuracy').textContent = 
                    stats.average_accuracy ? (stats.average_accuracy * 100).toFixed(1) + '%' : '0%';
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
    
    // Load joined date
    if (user.created_at) {
        const joinedEl = document.getElementById('infoJoined');
        if (joinedEl) {
            const date = new Date(user.created_at);
            joinedEl.textContent = date.toLocaleDateString('sr-RS');
        }
    }
    
    // Load results
    loadResults();
}

// Eksportuj loadProfile na window objekat da bude dostupan globalno
window.loadProfile = loadProfile;

async function loadResults() {
    const resultsList = document.getElementById('resultsList');
    if (!resultsList) return;
    
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    const userId = localStorage.getItem('userId') || userData.id;
    
    try {
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/user/results?user_id=${userId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const results = await response.json();
            if (results && results.length > 0) {
                resultsList.innerHTML = results.map(result => `
                    <div class="result-item">
                        <div class="result-info">
                            <h3>${result.quiz_title || 'Kviz'}</h3>
                            <p>Datum: ${new Date(result.completed_at).toLocaleDateString('sr-RS')}</p>
                        </div>
                        <div class="result-score">${result.score || 0}%</div>
                    </div>
                `).join('');
            } else {
                resultsList.innerHTML = '<p class="no-results">Nemate još uvek rezultata</p>';
            }
        } else {
            resultsList.innerHTML = '<p class="no-results">Nemate još uvek rezultata</p>';
        }
    } catch (error) {
        console.error('Error loading results:', error);
        resultsList.innerHTML = '<p class="no-results">Greška pri učitavanju rezultata</p>';
    }
}

async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    
    if (!oldPassword || !newPassword || !confirmPassword) {
        alert('Molimo popunite sva polja');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        alert('Nove lozinke se ne poklapaju');
        return;
    }
    
    if (newPassword.length < 6) {
        alert('Lozinka mora imati najmanje 6 karaktera');
        return;
    }
    
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    const userId = localStorage.getItem('userId') || userData.id;
    
    try {
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/user/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                old_password: oldPassword,
                new_password: newPassword
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                alert('Lozinka je uspešno promenjena!');
                document.getElementById('oldPassword').value = '';
                document.getElementById('newPassword').value = '';
                document.getElementById('confirmNewPassword').value = '';
            } else {
                alert(result.message || 'Greška pri promeni lozinke');
            }
        } else {
            alert('Greška pri promeni lozinke');
        }
    } catch (error) {
        console.error('Error changing password:', error);
        alert('Greška pri promeni lozinke. Proverite konekciju.');
    }
}

function handleLogout() {
    localStorage.removeItem('userData');
    localStorage.removeItem('userId');
    localStorage.removeItem('userData');
    window.location.href = '../pages/login.html';
}

function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🟢 PROFILE.JS - DOMContentLoaded pozvan');
    
    // Koristi checkAuth iz common.js
    if (typeof checkAuth === 'function') {
        console.log('🟢 PROFILE.JS - checkAuth funkcija je dostupna');
        if (!checkAuth()) {
            console.warn('🟢 PROFILE.JS - checkAuth() vratio false, prekidam');
            return;
        }
        console.log('🟢 PROFILE.JS - checkAuth() prošao, pozivam loadProfile()');
    } else {
        console.error('🟢 PROFILE.JS - checkAuth funkcija NIJE dostupna!');
        // Fallback - proveri direktno
        const userData = localStorage.getItem('userData');
        if (!userData) {
            console.warn('🟢 PROFILE.JS - Nema userData, preusmjeravam na login');
            window.location.href = '../pages/login.html';
            return;
        }
    }
    
    loadProfile();
    setupTabs();
    
    // Initialize theme manager
    if (typeof ThemeManager !== 'undefined') {
        ThemeManager.initTheme();
        
        // Setup theme selector when settings tab is clicked
        const settingsBtn = document.querySelector('[data-tab="settings"]');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                setTimeout(() => {
                    ThemeManager.setupThemeSelector();
                }, 100);
            });
        }
        
        // Also setup if settings tab is already active
        const settingsTab = document.getElementById('settingsTab');
        if (settingsTab && settingsTab.classList.contains('active')) {
            setTimeout(() => {
                ThemeManager.setupThemeSelector();
            }, 100);
        }
    }
    
    // Change password button
    const changePasswordBtn = document.getElementById('changePasswordBtn');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', changePassword);
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
});

