let boardData = { cols: [], tasks: [] };

async function loadBoard() {
    try {
        const response = await fetch('/api/board');
        if (!response.ok) throw new Error('Nie udało się pobrać tablicy');
        
        boardData = await response.json();
        displayBoard();
    } catch (error) {
        showNotification('Błąd podczas ładowania tablicy: ' + error.message, 'error');
    }
}

function displayBoard() {
    const board = document.getElementById('board');
    
    if (boardData.cols.length === 0) {
        board.innerHTML = '<div class="empty-state"><p>Brak kolumn</p></div>';
        return;
    }
    
    board.innerHTML = boardData.cols.map(col => {
        const colTasks = boardData.tasks.filter(t => t.col_id === col.id).sort((a, b) => a.ord - b.ord);
        
        return `
            <div class="column">
                <div class="column-header">
                    <h3>${escapeHtml(col.name)}</h3>
                    <span class="task-count">${colTasks.length}</span>
                </div>
                <button class="btn btn-primary btn-add" onclick="showAddTaskModal(${col.id})">+ Dodaj</button>
                <div class="tasks-list">
                    ${colTasks.map(task => `
                        <div class="task-card" data-task-id="${task.id}">
                            <div class="task-title">${escapeHtml(task.title)}</div>
                            <div class="task-actions">
                                ${getTaskActions(task, col)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function getTaskActions(task, currentCol) {
    const actions = [];
    const colIndex = boardData.cols.findIndex(c => c.id === currentCol.id);
    
    if (colIndex > 0) {
        const prevCol = boardData.cols[colIndex - 1];
        actions.push(`<button class="btn-move" onclick="moveTask(${task.id}, ${prevCol.id})" title="Przenieś do ${prevCol.name}">←</button>`);
    }
    
    if (colIndex < boardData.cols.length - 1) {
        const nextCol = boardData.cols[colIndex + 1];
        actions.push(`<button class="btn-move" onclick="moveTask(${task.id}, ${nextCol.id})" title="Przenieś do ${nextCol.name}">→</button>`);
    }
    
    return actions.join('');
}

function showAddTaskModal(colId) {
    document.getElementById('taskColId').value = colId;
    document.getElementById('addTaskModal').style.display = 'block';
}

function closeAddTaskModal() {
    document.getElementById('addTaskModal').style.display = 'none';
    document.getElementById('addTaskForm').reset();
}

async function addTask(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const task = {
        title: formData.get('title'),
        col_id: parseInt(formData.get('col_id'))
    };
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(task)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania zadania');
        }
        
        showNotification('Zadanie dodane!', 'success');
        closeAddTaskModal();
        loadBoard();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function moveTask(taskId, newColId) {
    try {
        // Get tasks in target column to determine new ord
        const targetTasks = boardData.tasks.filter(t => t.col_id === newColId);
        const newOrd = targetTasks.length > 0 ? Math.max(...targetTasks.map(t => t.ord)) + 1 : 1;
        
        const response = await fetch(`/api/tasks/${taskId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                col_id: newColId,
                ord: newOrd
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd przenoszenia zadania');
        }
        
        showNotification('Zadanie przeniesione!', 'success');
        loadBoard();
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
    const modal = document.getElementById('addTaskModal');
    if (event.target === modal) {
        closeAddTaskModal();
    }
}

document.addEventListener('DOMContentLoaded', loadBoard);
