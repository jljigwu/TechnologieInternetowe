async function loadPosts() {
    try {
        const response = await fetch('/api/posts');
        if (!response.ok) throw new Error('Nie udało się pobrać postów');
        
        const posts = await response.json();
        displayPosts(posts);
    } catch (error) {
        showNotification('Błąd podczas ładowania postów: ' + error.message, 'error');
    }
}

function displayPosts(posts) {
    const container = document.getElementById('postsContainer');
    
    if (posts.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak postów</p></div>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="post-card">
            <h3>${escapeHtml(post.title)}</h3>
            <p class="post-body">${escapeHtml(post.body)}</p>
            <div class="post-footer">
                <span class="post-date">${formatDate(post.created_at)}</span>
                <a href="/post/${post.id}" class="btn btn-primary btn-small">Zobacz komentarze</a>
            </div>
        </div>
    `).join('');
}

function showAddPostModal() {
    document.getElementById('addPostModal').style.display = 'block';
}

function closeAddPostModal() {
    document.getElementById('addPostModal').style.display = 'none';
    document.getElementById('addPostForm').reset();
}

async function addPost(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const post = {
        title: formData.get('title'),
        body: formData.get('body')
    };
    
    try {
        const response = await fetch('/api/posts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(post)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania posta');
        }
        
        showNotification('Post dodany pomyślnie!', 'success');
        closeAddPostModal();
        loadPosts();
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
    const modal = document.getElementById('addPostModal');
    if (event.target === modal) {
        closeAddPostModal();
    }
}

document.addEventListener('DOMContentLoaded', loadPosts);
