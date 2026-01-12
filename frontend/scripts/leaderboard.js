// Leaderboard JavaScript
// =======================
// API_BASE_URL is already defined in common.js

console.log('🟠 LEADERBOARD.JS SE UČITAVA!');

async function loadLeaderboard() {
    console.log('🟠 LEADERBOARD.JS - loadLeaderboard() pozvan');
    
    const body = document.getElementById('leaderboardBody');
    const topThree = document.getElementById('topThree');
    const userPosition = document.getElementById('userPosition');
    
    if (!body) {
        console.error('🟠 LEADERBOARD.JS - leaderboardBody nije pronađen!');
        return;
    }
    
    body.innerHTML = '<tr><td colspan="6" class="loading">Učitavanje leaderboard-a...</td></tr>';
    
    try {
        const apiUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://127.0.0.1:5000';
        const response = await fetch(`${apiUrl}/api/leaderboard`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Greška pri učitavanju leaderboard-a');
        }
        
        const leaderboard = await response.json();
        console.log('🟠 LEADERBOARD.JS - Primljen leaderboard:', leaderboard);
        console.log('🟠 LEADERBOARD.JS - Leaderboard length:', leaderboard ? leaderboard.length : 0);
        
        if (!leaderboard || leaderboard.length === 0) {
            // Nema rezultata
            body.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 3rem; color: var(--theme-text-secondary, #B3B3B3);">Još niko nije radio kvizove</td></tr>';
            if (topThree) topThree.innerHTML = '';
            if (userPosition) userPosition.style.display = 'none';
            return;
        }
        
        // Show top 3
        if (topThree && leaderboard.length >= 3) {
            const top3 = leaderboard.slice(0, 3);
            topThree.innerHTML = `
                <div class="podium-item second">
                    <div class="podium-rank">2</div>
                    <div class="podium-avatar">${top3[1].username[0].toUpperCase()}</div>
                    <div class="podium-name">${top3[1].username}</div>
                    <div class="podium-score">${top3[1].leaderboard_score.toFixed(0)}</div>
                </div>
                <div class="podium-item first">
                    <div class="podium-rank">1</div>
                    <div class="podium-avatar">${top3[0].username[0].toUpperCase()}</div>
                    <div class="podium-name">${top3[0].username}</div>
                    <div class="podium-score">${top3[0].leaderboard_score.toFixed(0)}</div>
                </div>
                <div class="podium-item third">
                    <div class="podium-rank">3</div>
                    <div class="podium-avatar">${top3[2].username[0].toUpperCase()}</div>
                    <div class="podium-name">${top3[2].username}</div>
                    <div class="podium-score">${top3[2].leaderboard_score.toFixed(0)}</div>
                </div>
            `;
        } else if (topThree) {
            topThree.innerHTML = '';
        }
        
        // Show full leaderboard
        body.innerHTML = leaderboard.map((user, index) => `
            <tr>
                <td>${user.rank}</td>
                <td>${user.username}</td>
                <td>${user.total_quizzes}</td>
                <td>${user.total_score}</td>
                <td>${user.average_accuracy.toFixed(1)}%</td>
                <td>${user.leaderboard_score.toFixed(0)}</td>
            </tr>
        `).join('');
        
        // Show user position if logged in
        const userData = getUserData();
        if (userData && userData.id && userPosition) {
            const userRank = leaderboard.findIndex(u => u.username === userData.username);
            if (userRank !== -1) {
                const userEntry = leaderboard[userRank];
                userPosition.style.display = 'block';
                document.getElementById('userPositionContent').innerHTML = `
                    <div class="user-position-info">
                        <div class="position-rank">#${userEntry.rank}</div>
                        <div class="position-details">
                            <p><strong>Korisnik:</strong> ${userEntry.username}</p>
                            <p><strong>Kvizova:</strong> ${userEntry.total_quizzes}</p>
                            <p><strong>Score:</strong> ${userEntry.total_score}</p>
                            <p><strong>Tačnost:</strong> ${userEntry.average_accuracy.toFixed(1)}%</p>
                        </div>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('🟠 LEADERBOARD.JS - Error loading leaderboard:', error);
        body.innerHTML = `<tr><td colspan="6" style="color: #ff0000;">Greška: ${error.message}</td></tr>`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🟠 LEADERBOARD.JS - DOMContentLoaded pozvan');
    
    if (typeof checkAuth === 'function') {
        if (!checkAuth()) return;
    }
    
    loadLeaderboard();
});
