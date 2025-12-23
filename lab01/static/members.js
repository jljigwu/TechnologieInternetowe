async function loadMembers() {
    try {
        const response = await fetch('/api/members');
        if (!response.ok) throw new Error('Nie udało się pobrać członków');
        
        const members = await response.json();
        displayMembers(members);
    } catch (error) {
        showNotification('Błąd podczas ładowania członków: ' + error.message, 'error');
    }
}

function displayMembers(members) {
    const container = document.getElementById('membersContainer');
    
    if (members.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak członków w systemie</p></div>';
        return;
    }
    
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Imię i Nazwisko</th>
                    <th>Email</th>
                </tr>
            </thead>
            <tbody>
                ${members.map(member => `
                    <tr>
                        <td>${member.id}</td>
                        <td>${escapeHtml(member.name)}</td>
                        <td>${escapeHtml(member.email)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

document.getElementById('addMemberForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const member = {
        name: document.getElementById('memberName').value.trim(),
        email: document.getElementById('memberEmail').value.trim()
    };
    
    try {
        const response = await fetch('/api/members', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(member)
        });
        
        if (!response.ok) {
            const error = await response.json();
            if (response.status === 409) {
                throw new Error('Ten adres email jest już zarejestrowany');
            }
            throw new Error(error.detail || 'Nie udało się dodać członka');
        }
        
        showNotification('Członek został dodany pomyślnie!', 'success');
        e.target.reset();
        loadMembers();
    } catch (error) {
        showNotification('Błąd: ' + error.message, 'error');
    }
});

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
loadMembers();
