let currentAuthor = '';

async function loadBooks() {
    try {
        const url = currentAuthor 
            ? `/api/books?author=${encodeURIComponent(currentAuthor)}` 
            : '/api/books';
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Nie udało się pobrać książek');
        
        const books = await response.json();
        displayBooks(books);
    } catch (error) {
        showNotification('Błąd podczas ładowania książek: ' + error.message, 'error');
    }
}

function displayBooks(books) {
    const container = document.getElementById('booksContainer');
    
    if (books.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Nie znaleziono książek</p></div>';
        return;
    }
    
    container.innerHTML = books.map(book => `
        <div class="book-card">
            <h3>${escapeHtml(book.title)}</h3>
            <p><strong>Autor:</strong> ${escapeHtml(book.author)}</p>
            <p><strong>Łącznie egzemplarzy:</strong> ${book.copies}</p>
            <div class="availability ${book.available > 0 ? 'available' : 'unavailable'}">
                ${book.available > 0 
                    ? `✓ Dostępne: ${book.available}` 
                    : '✗ Niedostępne'}
            </div>
        </div>
    `).join('');
}

async function loadMembers() {
    try {
        const response = await fetch('/api/members');
        if (!response.ok) throw new Error('Nie udało się pobrać członków');
        
        const members = await response.json();
        const select = document.getElementById('borrowMember');
        
        select.innerHTML = '<option value="">Wybierz członka...</option>' +
            members.map(m => `<option value="${m.id}">${escapeHtml(m.name)}</option>`).join('');
    } catch (error) {
        showNotification('Błąd podczas ładowania członków: ' + error.message, 'error');
    }
}

async function loadBooksForBorrow() {
    try {
        const response = await fetch('/api/books');
        if (!response.ok) throw new Error('Nie udało się pobrać książek');
        
        const books = await response.json();
        const select = document.getElementById('borrowBook');
        
        const availableBooks = books.filter(b => b.available > 0);
        select.innerHTML = '<option value="">Wybierz książkę...</option>' +
            availableBooks.map(b => 
                `<option value="${b.id}">${escapeHtml(b.title)} (${b.available} dostępne)</option>`
            ).join('');
    } catch (error) {
        showNotification('Błąd podczas ładowania książek: ' + error.message, 'error');
    }
}

function filterBooks() {
    currentAuthor = document.getElementById('authorFilter').value.trim();
    loadBooks();
}

function clearFilter() {
    document.getElementById('authorFilter').value = '';
    currentAuthor = '';
    loadBooks();
}

document.getElementById('addBookForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const book = {
        title: document.getElementById('bookTitle').value.trim(),
        author: document.getElementById('bookAuthor').value.trim(),
        copies: parseInt(document.getElementById('bookCopies').value)
    };
    
    try {
        const response = await fetch('/api/books', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(book)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Nie udało się dodać książki');
        }
        
        showNotification('Książka została dodana pomyślnie!', 'success');
        e.target.reset();
        loadBooks();
        loadBooksForBorrow();
    } catch (error) {
        showNotification('Błąd: ' + error.message, 'error');
    }
});

document.getElementById('borrowForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const loan = {
        member_id: parseInt(document.getElementById('borrowMember').value),
        book_id: parseInt(document.getElementById('borrowBook').value),
        days: parseInt(document.getElementById('borrowDays').value)
    };
    
    try {
        const response = await fetch('/api/loans/borrow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(loan)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Nie udało się wypożyczyć książki');
        }
        
        showNotification('Książka została wypożyczona pomyślnie!', 'success');
        e.target.reset();
        loadBooks();
        loadBooksForBorrow();
    } catch (error) {
        showNotification('Błąd: ' + error.message, 'error');
    }
});

// Allow Enter key to trigger filter
document.getElementById('authorFilter').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        filterBooks();
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
loadBooks();
loadMembers();
loadBooksForBorrow();
