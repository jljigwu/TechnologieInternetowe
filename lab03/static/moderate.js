async function loadPendingComments() {
    try {
        const response = await fetch('/api/comments/pending');
        if (!response.ok) throw new Error('Nie udało się pobrać komentarzy');
        
        const comments = await response.json();
        displayPendingComments(comments);
    } catch (error) {
        showNotification('Błąd podczas ładowania komentarzy: ' + error.message, 'error');
    }
}

function displayPendingComments(comments) {
    const container = document.getElementById('pendingContainer');
    
    if (comments.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak komentarzy oczekujących na moderację</p></div>';
        return;
    }
    
    container.innerHTML = comments.map(comment => `
        <div class="pending-card">
            <div class="pending-header">
                <div>
                    <strong>${escapeHtml(comment.author)}</strong>
                    <span class="comment-date">${formatDate(comment.created_at)}</span>
                </div>
                <button class="btn btn-success btn-small" onclick="approveComment(${comment.id})">✓ Zatwierdź</button>
            </div>
            <p class="post-reference">Post: <em>${escapeHtml(comment.post_title)}</em></p>
            <p class="comment-body">${escapeHtml(comment.body)}</p>
        </div>
    `).join('');
}

async function approveComment(commentId) {
    if (!confirm('Czy na pewno chcesz zatwierdzić ten komentarz?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/comments/${commentId}/approve`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd zatwierdzania komentarza');
        }
        
        showNotification('Komentarz zatwierdzony!', 'success');
        loadPendingComments();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('pl-PL');
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

document.addEventListener('DOMContentLoaded', loadPendingComments);
