// Authentication JavaScript
// ========================

console.log('🔴 AUTH.JS FAJL SE UČITAVA!');

const API_BASE_URL = 'http://127.0.0.1:5000'; // REST API endpoint

console.log('🔴 API_BASE_URL:', API_BASE_URL);

// Check if user is already logged in (bez JWT)
function checkAuth() {
    const userData = localStorage.getItem('userData');
    if (userData) {
        try {
            const user = JSON.parse(userData);
            if (user && user.id) {
                window.location.href = "../pages/dashboard.html";
            }
        } catch (e) {
            // Invalid userData, continue to login
        }
    }
}

// Login function
async function handleLogin(event) {
    event.preventDefault();
    console.log('🔵 handleLogin pozvan');
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const remember = document.getElementById('remember')?.checked || false;
    
    console.log('🔵 Username:', username, 'Password length:', password.length);
    
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    
    if (!errorDiv || !successDiv) {
        console.error('❌ ErrorDiv ili SuccessDiv nisu pronađeni!');
        return;
    }
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    try {
        console.log('🔵 Šaljem zahtev na:', `${API_BASE_URL}/api/login`);
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        console.log('Login response:', data);
        
        if (response.ok && data.success) {
            // Proveri da li postoji user objekat
            if (!data.user || !data.user.id) {
                console.error('Backend nije vratio user podatke:', data);
                errorDiv.textContent = 'Greška: Backend nije vratio korisničke podatke.';
                errorDiv.style.display = 'block';
                return;
            }
            
            localStorage.setItem('userData', JSON.stringify(data.user));
            localStorage.setItem('userId', data.user.id.toString());
            
            console.log('✓ Korisnik prijavljen:', data.user.username, 'ID:', data.user.id);
            console.log('✓ userData u localStorage:', localStorage.getItem('userData'));
            console.log('✓ userId u localStorage:', localStorage.getItem('userId'));
            
            successDiv.textContent = data.message;
            successDiv.style.display = 'block';
            
            setTimeout(() => {
                window.location.href = "../pages/dashboard.html";
            }, 1000);
        } else {
            errorDiv.textContent = data.message || 'Greška pri prijavljivanju';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        // Ne koristi fallback - prikaži grešku
        console.error('API error:', error);
        errorDiv.textContent = 'Greška pri povezivanju sa serverom. Proverite da li je backend server pokrenut.';
        errorDiv.style.display = 'block';
    }
}

// Register function
async function handleRegister(event) {
    event.preventDefault();
    console.log('🟢 handleRegister pozvan');
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const terms = document.getElementById('terms').checked;
    
    console.log('🟢 Username:', username, 'Email:', email, 'Password length:', password.length);
    
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    
    if (!errorDiv || !successDiv) {
        console.error('❌ ErrorDiv ili SuccessDiv nisu pronađeni!');
        return;
    }
    
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    // Validation
    if (password !== confirmPassword) {
        console.log('❌ Lozinke se ne poklapaju');
        errorDiv.textContent = 'Lozinke se ne poklapaju';
        errorDiv.style.display = 'block';
        return;
    }
    
    if (!terms) {
        console.log('❌ Terms nisu prihvaćeni');
        errorDiv.textContent = 'Morate prihvatiti uslove korišćenja';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        console.log('🟢 Šaljem zahtev na:', `${API_BASE_URL}/api/register`);
        const response = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password, confirmPassword })
        });
        
        const data = await response.json();
        console.log('Register response:', data);
        
        if (response.ok && data.success) {
            // Proveri da li postoji user objekat
            if (!data.user || !data.user.id) {
                console.error('Backend nije vratio user podatke:', data);
                errorDiv.textContent = 'Greška: Backend nije vratio korisničke podatke.';
                errorDiv.style.display = 'block';
                return;
            }
            
            localStorage.setItem('userData', JSON.stringify(data.user));
            localStorage.setItem('userId', data.user.id.toString());
            
            console.log('✓ Korisnik registrovan:', data.user.username, 'ID:', data.user.id);
            console.log('✓ userData u localStorage:', localStorage.getItem('userData'));
            console.log('✓ userId u localStorage:', localStorage.getItem('userId'));
            
            successDiv.textContent = data.message;
            successDiv.style.display = 'block';
            
            setTimeout(() => {
                window.location.href = "../pages/dashboard.html";
            }, 1000);
        } else {
            errorDiv.textContent = data.message || 'Greška pri registraciji';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        // Ne koristi fallback - prikaži grešku
        console.error('API error:', error);
        errorDiv.textContent = 'Greška pri povezivanju sa serverom. Proverite da li je backend server pokrenut.';
        errorDiv.style.display = 'block';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 Auth.js učitano');
    checkAuth();
    
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    console.log('📋 Login form pronađen:', !!loginForm);
    console.log('📋 Register form pronađen:', !!registerForm);
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
        console.log('✓ Login form event listener dodat');
    } else {
        console.error('❌ Login form nije pronađen!');
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        console.log('✓ Register form event listener dodat');
    } else {
        console.error('❌ Register form nije pronađen!');
    }
});

