async function loadCart() {
    try {
        const response = await fetch('/api/cart');
        if (!response.ok) throw new Error('Nie udało się pobrać koszyka');
        
        const cart = await response.json();
        displayCart(cart);
        updateCartCount();
    } catch (error) {
        showNotification('Błąd podczas ładowania koszyka: ' + error.message, 'error');
    }
}

function displayCart(cart) {
    const container = document.getElementById('cartContainer');
    const summary = document.getElementById('cartSummary');
    const totalElement = document.getElementById('cartTotal');
    
    if (cart.items.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Koszyk jest pusty</p><a href="/" class="btn btn-primary">Przejdź do produktów</a></div>';
        summary.style.display = 'none';
        return;
    }
    
    container.innerHTML = `
        <div class="cart-items">
            ${cart.items.map(item => `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <h3>${escapeHtml(item.product_name)}</h3>
                        <p class="item-price">${item.price.toFixed(2)} PLN</p>
                    </div>
                    <div class="cart-item-actions">
                        <div class="qty-control">
                            <button class="btn-qty" onclick="updateQuantity(${item.product_id}, ${item.qty - 1})">-</button>
                            <input type="number" value="${item.qty}" min="1" onchange="updateQuantity(${item.product_id}, this.value)" class="qty-input">
                            <button class="btn-qty" onclick="updateQuantity(${item.product_id}, ${item.qty + 1})">+</button>
                        </div>
                        <div class="item-subtotal">${item.subtotal.toFixed(2)} PLN</div>
                        <button class="btn btn-danger btn-small" onclick="removeFromCart(${item.product_id})">Usuń</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    totalElement.textContent = `${cart.total.toFixed(2)} PLN`;
    summary.style.display = 'block';
}

async function updateQuantity(productId, newQty) {
    newQty = parseInt(newQty);
    
    if (newQty < 1) {
        showNotification('Ilość musi być większa niż 0', 'error');
        loadCart(); // Reload to reset input
        return;
    }
    
    try {
        const response = await fetch('/api/cart/item', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: productId,
                qty: newQty
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd aktualizacji ilości');
        }
        
        loadCart();
    } catch (error) {
        showNotification(error.message, 'error');
        loadCart();
    }
}

async function removeFromCart(productId) {
    if (!confirm('Czy na pewno chcesz usunąć ten produkt z koszyka?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/cart/item/${productId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd usuwania produktu');
        }
        
        showNotification('Produkt usunięty z koszyka', 'success');
        loadCart();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function checkout() {
    if (!confirm('Czy na pewno chcesz złożyć zamówienie?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/checkout', {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd składania zamówienia');
        }
        
        const result = await response.json();
        showNotification(`Zamówienie złożone! Numer zamówienia: ${result.order_id}, Kwota: ${result.total.toFixed(2)} PLN`, 'success');
        
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function updateCartCount() {
    try {
        const response = await fetch('/api/cart');
        if (response.ok) {
            const cart = await response.json();
            const count = cart.items.reduce((sum, item) => sum + item.qty, 0);
            document.getElementById('cartCount').textContent = count;
        }
    } catch (error) {
        console.error('Error updating cart count:', error);
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

document.addEventListener('DOMContentLoaded', loadCart);
