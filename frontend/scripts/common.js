// Common JavaScript for all pages
// ===============================

console.log('🔵 COMMON.JS SE UČITAVA!');

const API_BASE_URL = 'http://127.0.0.1:5000';

console.log('🔵 API_BASE_URL:', API_BASE_URL);

// Get user data from localStorage
function getUserData() {
    const userData = localStorage.getItem('userData');
    return userData ? JSON.parse(userData) : null;
}

// Check authentication (bez JWT)
function checkAuth() {
    const userData = getUserData();
    if (!userData || !userData.id) {
        localStorage.removeItem('userData');
        localStorage.removeItem('userId');
        window.location.href = "../pages/login.html";
        return false;
    }
    return true;
}

// Load username in navbar
function loadUsername() {
    console.log('🔵 loadUsername() pozvan');
    const user = getUserData();
    console.log('🔵 User data:', user);
    
    if (user && user.username) {
        console.log('🔵 Username:', user.username);
        const usernameElements = document.querySelectorAll('#usernameDisplay, .username');
        console.log('🔵 Pronađeno username elemenata:', usernameElements.length);
        
        usernameElements.forEach(el => {
            if (el && el.id === 'usernameDisplay') {
                console.log('🔵 Ažuriram #usernameDisplay sa:', user.username);
                el.textContent = user.username;
            } else if (el && !el.id) {
                // Only update if it's not already set
                if (el.textContent === 'Korisnik' || el.textContent.trim() === '') {
                    console.log('🔵 Ažuriram .username sa:', user.username);
                    el.textContent = user.username;
                }
            }
        });
    } else {
        console.warn('🔵 Nema user data ili username!');
    }
}

// Logout handler
function handleLogout() {
    localStorage.removeItem('userData');
    localStorage.removeItem('userId');
    localStorage.removeItem('selectedTheme');
    window.location.href = "../pages/login.html";
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔵 COMMON.JS - DOMContentLoaded pozvan');
    
    // Load username
    console.log('🔵 COMMON.JS - Pozivam loadUsername()...');
    loadUsername();
    
    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        console.log('🔵 COMMON.JS - Logout button pronađen, dodajem event listener');
        logoutBtn.addEventListener('click', handleLogout);
    } else {
        console.warn('🔵 COMMON.JS - Logout button nije pronađen!');
    }
    
    // Initialize theme
    if (typeof ThemeManager !== 'undefined') {
        console.log('🔵 COMMON.JS - ThemeManager je dostupan, inicijalizujem temu');
        ThemeManager.initTheme();
    } else {
        console.warn('🔵 COMMON.JS - ThemeManager nije dostupan!');
    }
});

