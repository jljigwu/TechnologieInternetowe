let notesData = [];
let searchTimeout = null;

async function loadNotes(query = '') {
    try {
        const url = query ? `/api/notes?q=${encodeURIComponent(query)}` : '/api/notes';
        const response = await fetch(url);
        if (!response.ok) throw new Error('Nie udało się pobrać notatek');
        
        const data = await response.json();
        notesData = data.notes;
        displayNotes();
    } catch (error) {
        showNotification('Błąd podczas ładowania notatek: ' + error.message, 'error');
    }
}

function displayNotes() {
    const notesList = document.getElementById('notesList');
    
    if (notesData.length === 0) {
        notesList.innerHTML = '<div class="empty-state"><p>Brak notatek</p></div>';
        return;
    }
    
    notesList.innerHTML = notesData.map(note => {
        const createdDate = new Date(note.created_at);
        const formattedDate = createdDate.toLocaleDateString('pl-PL') + ' ' + createdDate.toLocaleTimeString('pl-PL', {hour: '2-digit', minute: '2-digit'});
        
        const bodyPreview = note.body.length > 200 ? note.body.substring(0, 200) + '...' : note.body;
        
        return `
            <div class="note-card">
                <div class="note-header">
                    <h3>${escapeHtml(note.title)}</h3>
                    <span class="note-date">${formattedDate}</span>
                </div>
                <div class="note-body">
                    ${escapeHtml(bodyPreview)}
                </div>
                <div class="note-footer">
                    <div class="tags">
                        ${note.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                    <button class="btn-tag" onclick="showAssignTagsModal(${note.id})">+ Tag</button>
                </div>
            </div>
        `;
    }).join('');
}

function searchNotes() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const query = document.getElementById('searchInput').value.trim();
        loadNotes(query);
    }, 300);
}

function showAddNoteModal() {
    document.getElementById('addNoteModal').style.display = 'block';
}

function closeAddNoteModal() {
    document.getElementById('addNoteModal').style.display = 'none';
    document.getElementById('addNoteForm').reset();
}

async function addNote(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const note = {
        title: formData.get('title'),
        body: formData.get('body')
    };
    
    try {
        const response = await fetch('/api/notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(note)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania notatki');
        }
        
        showNotification('Notatka dodana!', 'success');
        closeAddNoteModal();
        loadNotes();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function showAssignTagsModal(noteId) {
    document.getElementById('tagNoteId').value = noteId;
    document.getElementById('assignTagsModal').style.display = 'block';
}

function closeAssignTagsModal() {
    document.getElementById('assignTagsModal').style.display = 'none';
    document.getElementById('assignTagsForm').reset();
}

async function assignTags(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const noteId = formData.get('note_id');
    const tagsInput = formData.get('tags');
    
    const tags = tagsInput.split(',').map(t => t.trim()).filter(t => t);
    
    if (tags.length === 0) {
        showNotification('Wprowadź przynajmniej jeden tag', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/notes/${noteId}/tags`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tags })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd przypisywania tagów');
        }
        
        showNotification('Tagi przypisane!', 'success');
        closeAssignTagsModal();
        loadNotes();
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
    const addModal = document.getElementById('addNoteModal');
    const tagsModal = document.getElementById('assignTagsModal');
    if (event.target === addModal) {
        closeAddNoteModal();
    }
    if (event.target === tagsModal) {
        closeAssignTagsModal();
    }
}

document.addEventListener('DOMContentLoaded', loadNotes);
