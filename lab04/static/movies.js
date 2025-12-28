async function loadMovies() {
    try {
        const response = await fetch('/api/movies');
        if (!response.ok) throw new Error('Nie udało się pobrać filmów');
        
        const movies = await response.json();
        displayMovies(movies);
    } catch (error) {
        showNotification('Błąd podczas ładowania filmów: ' + error.message, 'error');
    }
}

function displayMovies(movies) {
    const container = document.getElementById('moviesContainer');
    
    if (movies.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak filmów</p></div>';
        return;
    }
    
    container.innerHTML = movies.map((movie, index) => `
        <div class="movie-card">
            <div class="movie-rank">#${index + 1}</div>
            <div class="movie-info">
                <h3>${escapeHtml(movie.title)}</h3>
                <p class="movie-year">${movie.year}</p>
            </div>
            <div class="movie-rating">
                <div class="rating-score">
                    <span class="score">${movie.avg_score.toFixed(2)}</span>
                    <span class="stars">${getStars(movie.avg_score)}</span>
                </div>
                <div class="rating-votes">${movie.votes} ${movie.votes === 1 ? 'głos' : 'głosów'}</div>
            </div>
            <button class="btn btn-primary btn-small" onclick="showRateModal(${movie.id}, '${escapeHtml(movie.title)}')">Oceń</button>
        </div>
    `).join('');
}

function getStars(score) {
    const fullStars = Math.floor(score);
    const hasHalf = score % 1 >= 0.5;
    let stars = '⭐'.repeat(fullStars);
    if (hasHalf && fullStars < 5) stars += '½';
    return stars || '☆';
}

function showAddMovieModal() {
    document.getElementById('addMovieModal').style.display = 'block';
}

function closeAddMovieModal() {
    document.getElementById('addMovieModal').style.display = 'none';
    document.getElementById('addMovieForm').reset();
}

async function addMovie(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const movie = {
        title: formData.get('title'),
        year: parseInt(formData.get('year'))
    };
    
    try {
        const response = await fetch('/api/movies', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(movie)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania filmu');
        }
        
        showNotification('Film dodany pomyślnie!', 'success');
        closeAddMovieModal();
        loadMovies();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function showRateModal(movieId, movieTitle) {
    document.getElementById('rateMovieId').value = movieId;
    document.getElementById('rateMovieTitle').textContent = movieTitle;
    document.getElementById('rateMovieModal').style.display = 'block';
}

function closeRateModal() {
    document.getElementById('rateMovieModal').style.display = 'none';
    document.getElementById('rateMovieForm').reset();
}

async function submitRating(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const rating = {
        movie_id: parseInt(formData.get('movie_id')),
        score: parseInt(formData.get('score'))
    };
    
    try {
        const response = await fetch('/api/ratings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(rating)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania oceny');
        }
        
        showNotification('Ocena dodana pomyślnie!', 'success');
        closeRateModal();
        loadMovies();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.onclick = function(event) {
    const addModal = document.getElementById('addMovieModal');
    const rateModal = document.getElementById('rateMovieModal');
    if (event.target === addModal) {
        closeAddMovieModal();
    }
    if (event.target === rateModal) {
        closeRateModal();
    }
}

document.addEventListener('DOMContentLoaded', loadMovies);
