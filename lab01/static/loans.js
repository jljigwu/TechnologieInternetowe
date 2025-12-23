async function loadActiveLoans() {
    try {
        const response = await fetch('/api/loans');
        if (!response.ok) throw new Error('Nie udało się pobrać wypożyczeń');
        
        const loans = await response.json();
        const activeLoans = loans.filter(l => !l.return_date);
        
        displayActiveLoans(activeLoans);
    } catch (error) {
        showNotification('Błąd podczas ładowania aktywnych wypożyczeń: ' + error.message, 'error');
    }
}

function displayActiveLoans(loans) {
    const container = document.getElementById('activeLoansContainer');
    
    if (loans.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak aktywnych wypożyczeń</p></div>';
        return;
    }
    
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Członek</th>
                    <th>Książka</th>
                    <th>Data wypożyczenia</th>
                    <th>Termin zwrotu</th>
                    <th>Status</th>
                    <th>Akcja</th>
                </tr>
            </thead>
            <tbody>
                ${loans.map(loan => `
                    <tr>
                        <td>${loan.id}</td>
                        <td>${escapeHtml(loan.member_name)}</td>
                        <td>${escapeHtml(loan.book_title)}</td>
                        <td>${loan.loan_date}</td>
                        <td>${loan.due_date}</td>
                        <td><span class="badge badge-active">Aktywne</span></td>
                        <td>
                            <button onclick="returnBook(${loan.id})" class="btn btn-success btn-small">
                                Zwróć
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function loadReturnedLoans() {
    try {
        const response = await fetch('/api/loans');
        if (!response.ok) throw new Error('Nie udało się pobrać wypożyczeń');
        
        const loans = await response.json();
        const returnedLoans = loans.filter(l => l.return_date);
        displayReturnedLoans(returnedLoans);
    } catch (error) {
        showNotification('Błąd podczas ładowania zwróconych wypożyczeń: ' + error.message, 'error');
    }
}

function displayReturnedLoans(loans) {
    const container = document.getElementById('returnedLoansContainer');
    
    if (loans.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak zwróconych wypożyczeń w historii</p></div>';
        return;
    }
    
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Członek</th>
                    <th>Książka</th>
                    <th>Data wypożyczenia</th>
                    <th>Termin zwrotu</th>
                    <th>Data zwrotu</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${loans.map(loan => {
                    const wasLate = loan.return_date > loan.due_date;
                    return `
                        <tr>
                            <td>${loan.id}</td>
                            <td>${escapeHtml(loan.member_name)}</td>
                            <td>${escapeHtml(loan.book_title)}</td>
                            <td>${loan.loan_date}</td>
                            <td>${loan.due_date}</td>
                            <td>${loan.return_date}</td>
                            <td>
                                <span class="badge ${wasLate ? 'badge-overdue' : 'badge-returned'}">
                                    ${wasLate ? 'Zwrócone (po terminie)' : 'Zwrócone'}
                                </span>
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
}

async function returnBook(loanId) {
    if (!confirm('Czy na pewno chcesz zwrócić tę książkę?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/loans/return', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ loan_id: loanId })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Nie udało się zwrócić książki');
        }
        
        showNotification('Książka została zwrócona pomyślnie!', 'success');
        loadActiveLoans();
        loadReturnedLoans();
    } catch (error) {
        showNotification('Błąd: ' + error.message, 'error');
    }
}

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
loadActiveLoans();
loadReturnedLoans();
