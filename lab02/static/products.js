async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        if (!response.ok) throw new Error('Nie udało się pobrać produktów');
        
        const products = await response.json();
        displayProducts(products);
        updateCartCount();
    } catch (error) {
        showNotification('Błąd podczas ładowania produktów: ' + error.message, 'error');
    }
}

function displayProducts(products) {
    const container = document.getElementById('productsContainer');
    
    if (products.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Brak produktów w sklepie</p></div>';
        return;
    }
    
    container.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-icon">📦</div>
            <h3>${escapeHtml(product.name)}</h3>
            <p class="product-price">${product.price.toFixed(2)} PLN</p>
            <button class="btn btn-primary" onclick="addToCart(${product.id})">Dodaj do koszyka</button>
        </div>
    `).join('');
}

async function addToCart(productId) {
    try {
        const response = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: productId,
                qty: 1
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania do koszyka');
        }
        
        showNotification('Produkt dodany do koszyka!', 'success');
        updateCartCount();
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

function showAddProductModal() {
    document.getElementById('addProductModal').style.display = 'block';
}

function closeAddProductModal() {
    document.getElementById('addProductModal').style.display = 'none';
    document.getElementById('addProductForm').reset();
}

async function addProduct(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const product = {
        name: formData.get('name'),
        price: parseFloat(formData.get('price'))
    };
    
    try {
        const response = await fetch('/api/products', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(product)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Błąd dodawania produktu');
        }
        
        showNotification('Produkt dodany pomyślnie!', 'success');
        closeAddProductModal();
        loadProducts();
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

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('addProductModal');
    if (event.target === modal) {
        closeAddProductModal();
    }
}

// Load products on page load
document.addEventListener('DOMContentLoaded', loadProducts);
