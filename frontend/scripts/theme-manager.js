// Theme Manager - Global Theme System
// ====================================

const ThemeManager = {
    themes: {
        'red-dark': {
            name: 'Crvena Tamna',
            gradient: 'linear-gradient(135deg, #0a0a0a 0%, #1a0a0a 50%, #0a0a0a 100%)',
            primary: '#E50914',
            primaryDark: '#B20710',
            border: 'rgba(229, 9, 20, 0.2)',
            borderHover: 'rgba(229, 9, 20, 0.5)',
            navbarBorder: 'rgba(229, 9, 20, 0.2)',
            cardBg: 'linear-gradient(135deg, #141414 0%, #1a0a0a 50%, #141414 100%)',
            text: '#FFFFFF',
            textSecondary: '#B3B3B3',
            textMuted: '#808080'
        },
        'blue-dark': {
            name: 'Plava Tamna',
            gradient: 'linear-gradient(135deg, #0a0a14 0%, #0a1428 50%, #0a0a14 100%)',
            primary: '#0071EB',
            primaryDark: '#0051A3',
            border: 'rgba(0, 113, 235, 0.2)',
            borderHover: 'rgba(0, 113, 235, 0.5)',
            navbarBorder: 'rgba(0, 113, 235, 0.2)',
            cardBg: 'linear-gradient(135deg, #14141a 0%, #1a1a28 50%, #14141a 100%)',
            text: '#FFFFFF',
            textSecondary: '#B3B3B3',
            textMuted: '#808080'
        },
        'purple-dark': {
            name: 'Ljubičasta Tamna',
            gradient: 'linear-gradient(135deg, #0a0a14 0%, #1a0a28 50%, #0a0a14 100%)',
            primary: '#8B5CF6',
            primaryDark: '#7C3AED',
            border: 'rgba(139, 92, 246, 0.2)',
            borderHover: 'rgba(139, 92, 246, 0.5)',
            navbarBorder: 'rgba(139, 92, 246, 0.2)',
            cardBg: 'linear-gradient(135deg, #14141a 0%, #1a0a28 50%, #14141a 100%)',
            text: '#FFFFFF',
            textSecondary: '#B3B3B3',
            textMuted: '#808080'
        },
        'green-dark': {
            name: 'Zelena Tamna',
            gradient: 'linear-gradient(135deg, #0a140a 0%, #142814 50%, #0a140a 100%)',
            primary: '#46D369',
            primaryDark: '#2DB54F',
            border: 'rgba(70, 211, 105, 0.2)',
            borderHover: 'rgba(70, 211, 105, 0.5)',
            navbarBorder: 'rgba(70, 211, 105, 0.2)',
            cardBg: 'linear-gradient(135deg, #141a14 0%, #1a281a 50%, #141a14 100%)',
            text: '#FFFFFF',
            textSecondary: '#B3B3B3',
            textMuted: '#808080'
        },
        'orange-dark': {
            name: 'Narandžasta Tamna',
            gradient: 'linear-gradient(135deg, #140a0a 0%, #28140a 50%, #140a0a 100%)',
            primary: '#FFA500',
            primaryDark: '#FF8C00',
            border: 'rgba(255, 165, 0, 0.2)',
            borderHover: 'rgba(255, 165, 0, 0.5)',
            navbarBorder: 'rgba(255, 165, 0, 0.2)',
            cardBg: 'linear-gradient(135deg, #1a1414 0%, #281a14 50%, #1a1414 100%)',
            text: '#FFFFFF',
            textSecondary: '#B3B3B3',
            textMuted: '#808080'
        },
        'pink-dark': {
            name: 'Roze Tamna',
            gradient: 'linear-gradient(135deg, #140a14 0%, #281428 50%, #140a14 100%)',
            primary: '#FF1493',
            primaryDark: '#DC0F7A',
            border: 'rgba(255, 20, 147, 0.2)',
            borderHover: 'rgba(255, 20, 147, 0.5)',
            navbarBorder: 'rgba(255, 20, 147, 0.2)',
            cardBg: 'linear-gradient(135deg, #1a141a 0%, #281a28 50%, #1a141a 100%)',
            text: '#FFFFFF',
            textSecondary: '#B3B3B3',
            textMuted: '#808080'
        }
    },

    // Load saved theme or use default
    initTheme() {
        const savedTheme = localStorage.getItem('selectedTheme') || 'red-dark';
        this.applyTheme(savedTheme);
    },

    // Apply theme to entire page
    applyTheme(themeName) {
        const theme = this.themes[themeName];
        if (!theme) {
            console.error('Theme not found:', themeName);
            return;
        }

        // Set body attributes
        document.body.setAttribute('data-theme', themeName);
        // Background removed - using CSS background-image instead
        document.body.style.color = theme.text;

        // Update CSS variables
        document.documentElement.style.setProperty('--theme-primary', theme.primary);
        document.documentElement.style.setProperty('--theme-primary-dark', theme.primaryDark);
        document.documentElement.style.setProperty('--theme-gradient', theme.gradient);
        document.documentElement.style.setProperty('--theme-border', theme.border);
        document.documentElement.style.setProperty('--theme-border-hover', theme.borderHover);
        document.documentElement.style.setProperty('--theme-card-bg', theme.cardBg);
        document.documentElement.style.setProperty('--theme-text', theme.text);
        document.documentElement.style.setProperty('--theme-text-secondary', theme.textSecondary);
        document.documentElement.style.setProperty('--theme-text-muted', theme.textMuted);

        // Update navbar
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.style.borderBottomColor = theme.navbarBorder;
            navbar.style.background = `linear-gradient(180deg, rgba(10,10,10,0.95) 0%, rgba(26,10,10,0.9) 100%)`;
        }

        // Update all cards and containers
        document.querySelectorAll('.card, .quiz-form-container, .page-header, .welcome-section, .stat-card, .action-card, .activity-section, .quiz-card, .profile-container, .leaderboard-item, .results-container, .loading-content, .filters-section, .empty-state, .podium-section, .leaderboard-container, .user-position-card, .search-section').forEach(el => {
            el.style.background = theme.cardBg;
            el.style.borderColor = theme.border;
            el.style.color = theme.text;
        });
        
        // Update quiz card titles and other primary colored elements
        document.querySelectorAll('.quiz-title, .empty-state h2, .user-position-card h3, .podium-rank').forEach(el => {
            el.style.color = theme.primary;
        });
        
        // Update buttons with primary colors
        document.querySelectorAll('.btn-view, .btn-play, .rank-badge').forEach(btn => {
            btn.style.background = theme.primary;
            btn.style.color = theme.text;
        });
        
        // Update border buttons
        document.querySelectorAll('.btn-results').forEach(btn => {
            btn.style.borderColor = theme.primary;
            btn.style.color = theme.primary;
        });
        
        // Update table headers
        document.querySelectorAll('.leaderboard-table thead').forEach(thead => {
            thead.style.background = `linear-gradient(135deg, ${theme.primary} 0%, ${theme.primaryDark} 100%)`;
        });
        
        // Update podium avatars (except top 3 which keep gold/silver/bronze)
        document.querySelectorAll('.podium-avatar').forEach(avatar => {
            if (!avatar.closest('.podium-item.first') && 
                !avatar.closest('.podium-item.second') && 
                !avatar.closest('.podium-item.third')) {
                avatar.style.background = `linear-gradient(135deg, ${theme.primary} 0%, ${theme.primaryDark} 100%)`;
                avatar.style.boxShadow = `0 4px 15px ${theme.border.replace('0.2', '0.3')}`;
            }
        });

        // Update all buttons
        document.querySelectorAll('.btn-primary').forEach(btn => {
            btn.style.background = theme.primary;
            btn.style.color = theme.text;
        });

        // Update all links
        document.querySelectorAll('.nav-link.active').forEach(link => {
            link.style.color = theme.primary;
        });

        // Update all headings
        document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
            heading.style.color = theme.text;
        });

        // Update all text elements
        document.querySelectorAll('p, span, label, div').forEach(el => {
            if (!el.classList.contains('theme-preserve')) {
                el.style.color = theme.text;
            }
        });

        // Update inputs
        document.querySelectorAll('input, textarea, select').forEach(input => {
            input.style.background = '#2F2F2F';
            input.style.borderColor = '#333333';
            input.style.color = theme.text;
        });

        // Save to localStorage
        localStorage.setItem('selectedTheme', themeName);
    },

    // Setup theme selector on profile page
    setupThemeSelector() {
        const themeOptions = document.querySelectorAll('.theme-option');
        if (themeOptions.length === 0) return;

        // Load current theme and mark as active
        const currentTheme = localStorage.getItem('selectedTheme') || 'red-dark';
        this.updateThemeSelection(currentTheme);

        // Add click handlers
        themeOptions.forEach(option => {
            option.addEventListener('click', () => {
                const themeName = option.getAttribute('data-theme');
                this.applyTheme(themeName);
                this.updateThemeSelection(themeName);
                this.showNotification('Tema je uspešno promenjena!', 'success');
            });
        });
    },

    // Update theme selection UI
    updateThemeSelection(selectedTheme) {
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
            if (option.getAttribute('data-theme') === selectedTheme) {
                option.classList.add('active');
            }
        });
    },

    // Show notification
    showNotification(message, type = 'info') {
        // Remove existing notification
        const existing = document.querySelector('.theme-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `theme-notification theme-notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? '#46D369' : '#E50914'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 4px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            font-family: 'VT323', monospace;
            letter-spacing: 0.02em;
            font-weight: 600;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
};

// Auto-initialize theme on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        ThemeManager.initTheme();
    });
} else {
    ThemeManager.initTheme();
}
