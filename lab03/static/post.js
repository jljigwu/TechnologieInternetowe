let currentPostId = null;

async function loadPost() {
    const url = window.location.pathname;
    const postId = url.split('/').pop();
    currentPostId = parseInt(postId);
    
    try {
        const response = await fetch('/api/posts');
        if (!response.ok) throw new Error('Nie udało się pobrać posta');
        
        const posts = await response.json();
        const post = posts.find(p => p.id === currentPostId);
        
        if (!post) {
            throw new Error('Post nie został znaleziony');
        }
        
        displayPost(post);
        loadComments();
    } catch (error) {
        document.getElementById('postContainer').innerHTML = 
            `<div class="empty-state"><p>${error.message}</p><a href="/" class="btn btn-primary">Powrót</a></div>`;
    }
}

function displayPost(post) {
    const container = document.getElementById('postContainer');
    container.innerHTML = `
        <div class="post-detail">
            <h2>${escapeHtml(post.title)}</h2>
            <p class="post-date">${formatDate(post.created_at)}</p>
            <div class="post-content">${escapeHtml(post.body)}</div>
        </div>
    `;
    
    document.getElementById('commentsSection').style.display = 'block';
}

async function loadComments() {
    try {
        const response = await fetch(`/api/posts/${currentPostId}/comments`);
        if (!response.ok) throw new Error('Nie udało się pobrać komentarzy');
        
        const comments = await response.json();
        displayComments(comments);
    } catch (error) {
        showNotification('Błąd podczas ładowania komentarzy: ' + error.message, 'error');
    }
}

function displayComments(comments) {
    const container = document.getElementById('commentsContainer');
    
    if (comments.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak komentarzy. Bądź pierwszy!</p></div>';
        return;
    }
    
    container.innerHTML = comments.map(comment => `
        <div class="comment-card">
            <div class="comment-header">
                <strong>${escapeHtml(comment.author)}</strong>
                <span class="comment-date">${formatDate(comment.created_at)}</span>
            </div>
            <p class="comment-body">${escapeHtml(comment.body)}</p>
        </div>
    `).join('');
}

function showAddCommentModal() {
    document.getElementById('addCommentModal').style.display = 'block';
}

function closeAddCommentModal() {
    document.getElementById('addCommentModal').style.display = 'none';
    document.getElementById('addCommentForm').reset();
}

async function addComment(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const comment = {
        author: formData.get('author'),
        body: formData.get('body')
    };
    
    try {
        const response = await fetch(`/api/posts/${currentPostId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(comment)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania komentarza');
        }
        
        showNotification('Komentarz dodany! Zostanie opublikowany po zatwierdzeniu przez moderatora.', 'success');
        closeAddCommentModal();
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

window.onclick = function(event) {
    const modal = document.getElementById('addCommentModal');
    if (event.target === modal) {
        closeAddCommentModal();
    }
}

document.addEventListener('DOMContentLoaded', loadPost);
