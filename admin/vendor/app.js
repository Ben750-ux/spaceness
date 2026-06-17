const API_URL = '/vendor_api';

// Prévisualiser l'image du produit
function previewImage(url) {
    const preview = document.getElementById('image-preview');
    const img = document.getElementById('preview-img');
    
    if (url && url.trim()) {
        img.src = url;
        img.onload = () => { preview.style.display = 'block'; };
        img.onerror = () => { preview.style.display = 'none'; };
    } else {
        preview.style.display = 'none';
    }
}

// Check authentication on load
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    setupEventListeners();
});

async function checkAuth() {
    try {
        const res = await fetch(API_URL + '/check-auth', { credentials: 'include' });
        const data = await res.json();
        
        if (data.authenticated) {
            showDashboard(data.vendor);
            await loadAll();
        } else {
            showLogin();
        }
    } catch (err) {
        console.error('Auth check failed:', err);
        showLogin();
    }
}

function showLogin() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
}

function showDashboard(vendor) {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('shop-name').textContent = vendor.shop_name || vendor.name;
}

function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Shop form
    document.getElementById('shop-form').addEventListener('submit', handleShopUpdate);
    
    // Product form
    document.getElementById('product-form').addEventListener('submit', handleProductAdd);
}

// ============ AUTHENTIFICATION ============
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('login-error');
    
    console.log('Tentative de connexion...');
    console.log('API_URL:', API_URL);
    
    try {
        const url = API_URL + '/login';
        console.log('URL:', url);
        
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });
        
        console.log('Response status:', res.status);
        const data = await res.json();
        console.log('Response data:', data);
        
        if (data.success) {
            errorEl.textContent = '';
            showDashboard(data.vendor);
            await loadAll();
        } else {
            errorEl.textContent = data.error || 'Identifiants invalides';
        }
    } catch (err) {
        errorEl.textContent = 'Erreur de connexion';
        console.error('Erreur:', err);
    }
}

async function logout() {
    try {
        await fetch(API_URL + '/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (err) {
        console.error(err);
    }
    showLogin();
}

// ============ CHARGER LES DONNÉES ============
async function loadAll() {
    await Promise.all([
        loadStats(),
        loadShop(),
        loadProducts(),
        loadOrders(),
        loadMessages()
    ]);
}

async function loadStats() {
    try {
        const res = await fetch(API_URL + '/stats', { credentials: 'include' });
        const data = await res.json();
        document.getElementById('stat-products').textContent = data.total_products || 0;
        document.getElementById('stat-orders').textContent = data.total_orders || 0;
        document.getElementById('stat-revenue').textContent = (data.total_revenue || 0).toFixed(2) + ' cr';
        document.getElementById('stat-subscribers').textContent = data.total_subscribers || 0;
    } catch (err) {
        console.error('Stats error:', err);
    }
}

async function loadShop() {
    try {
        const res = await fetch(API_URL + '/shop', { credentials: 'include' });
        if (!res.ok) return;
        const shop = await res.json();
        
        document.getElementById('shop-name-input').value = shop.shop_name || '';
        document.getElementById('shop-description').value = shop.description || '';
        document.getElementById('shop-contact').value = shop.contact_info || '';
        document.getElementById('shop-logo').value = shop.logo_url || '';
        document.getElementById('shop-banner').value = shop.banner_url || '';
    } catch (err) {
        console.error('Shop error:', err);
    }
}

async function loadProducts() {
    try {
        const res = await fetch(API_URL + '/products', { credentials: 'include' });
        const products = await res.json();
        const tbody = document.getElementById('products-body');
        
        if (products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#636e72;padding:40px;"><i class="fas fa-box-open" style="font-size:32px;opacity:0.3;display:block;margin-bottom:10px;"></i>Aucun produit</td></tr>';
            return;
        }
        
        tbody.innerHTML = products.map(p => `
            <tr>
                <td><strong>#${p.id}</strong></td>
                <td>${p.name}</td>
                <td><span style="background:#e9ecef;padding:4px 10px;border-radius:20px;font-size:12px;">${p.category}</span></td>
                <td><strong style="color:#00b894;">${parseFloat(p.price).toFixed(2)} cr</strong></td>
                <td>${p.stock > 0 ? p.stock : '<span style="color:#e74c3c;">Épuisé</span>'}</td>
                <td><span class="status ${p.is_active ? 'active' : 'cancelled'}">${p.is_active ? '✓ Actif' : '✗ Inactif'}</span></td>
                <td>
                    <button class="btn btn-warning btn-small" onclick="openProductModal(${p.id}, ${p.stock}, ${p.is_active})"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-danger btn-small" onclick="deleteProduct(${p.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Products error:', err);
    }
}

async function loadOrders() {
    try {
        const res = await fetch(API_URL + '/orders', { credentials: 'include' });
        const orders = await res.json();
        const tbody = document.getElementById('orders-body');
        
        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#636e72;padding:40px;"><i class="fas fa-shopping-cart" style="font-size:32px;opacity:0.3;display:block;margin-bottom:10px;"></i>Aucune commande</td></tr>';
            return;
        }
        
        tbody.innerHTML = orders.map(o => `
            <tr>
                <td><strong>#${o.id}</strong></td>
                <td><i class="fas fa-user"></i> ${o.client_name_masked || 'Client'}</td>
                <td>${o.product_name}</td>
                <td><strong>${o.quantity}</strong></td>
                <td><strong style="color:#00b894;">${parseFloat(o.total_amount).toFixed(2)} cr</strong></td>
                <td><span class="status ${o.status}">${o.status}</span></td>
                <td><i class="far fa-calendar-alt"></i> ${new Date(o.created_at).toLocaleDateString('fr-FR')}</td>
                <td>
                    <select class="btn btn-small" style="padding:6px 12px;" onchange="updateOrderStatus(${o.id}, this.value)">
                        <option value="pending" ${o.status === 'pending' ? 'selected' : ''}>En attente</option>
                        <option value="confirmed" ${o.status === 'confirmed' ? 'selected' : ''}>Confirmée</option>
                        <option value="shipped" ${o.status === 'shipped' ? 'selected' : ''}>Expédiée</option>
                        <option value="delivered" ${o.status === 'delivered' ? 'selected' : ''}>Livrée</option>
                        <option value="cancelled" ${o.status === 'cancelled' ? 'selected' : ''}>Annulée</option>
                    </select>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Orders error:', err);
    }
}

// ============ NAVIGATION ============
function showTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelector(`.tab[onclick="showTab('${tab}')"]`).classList.add('active');
    document.getElementById(`section-${tab}`).classList.add('active');
}

// ============ BOUTIQUE ============
async function handleShopUpdate(e) {
    e.preventDefault();
    const statusEl = document.getElementById('shop-status');
    
    const data = {
        shop_name: document.getElementById('shop-name-input').value.trim(),
        description: document.getElementById('shop-description').value.trim(),
        contact_info: document.getElementById('shop-contact').value.trim(),
        logo_url: document.getElementById('shop-logo').value.trim(),
        banner_url: document.getElementById('shop-banner').value.trim()
    };
    
    try {
        const res = await fetch(API_URL + '/shop', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await res.json();
        
        if (result.success) {
            statusEl.textContent = '✓ Enregistré';
            statusEl.style.color = '#00b894';
            setTimeout(() => { statusEl.textContent = ''; }, 3000);
        } else {
            statusEl.textContent = '✗ Erreur: ' + result.message;
            statusEl.style.color = '#e74c3c';
        }
    } catch (err) {
        statusEl.textContent = '✗ Erreur de connexion';
        statusEl.style.color = '#e74c3c';
    }
}

// ============ PRODUITS ============
async function handleProductAdd(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('product-name').value.trim(),
        category: document.getElementById('product-category').value.trim() || 'General',
        price: parseFloat(document.getElementById('product-price').value),
        stock: parseInt(document.getElementById('product-stock').value),
        description: document.getElementById('product-description').value.trim(),
        image_url: document.getElementById('product-image').value.trim()
    };
    
    try {
        const res = await fetch(API_URL + '/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await res.json();
        
        if (result.success) {
            document.getElementById('product-form').reset();
            await Promise.all([loadProducts(), loadStats()]);
            alert('Produit ajouté avec succès !');
        } else {
            alert(result.message || 'Erreur lors de l\'ajout');
        }
    } catch (err) {
        alert('Erreur de connexion');
    }
}

function openProductModal(productId, stock, isActive) {
    document.getElementById('edit-product-id').value = productId;
    document.getElementById('edit-stock').value = stock;
    document.getElementById('edit-active').checked = isActive;
    document.getElementById('product-modal').style.display = 'block';
}

function closeProductModal() {
    document.getElementById('product-modal').style.display = 'none';
}

async function saveProduct() {
    const productId = document.getElementById('edit-product-id').value;
    const stock = parseInt(document.getElementById('edit-stock').value);
    const isActive = document.getElementById('edit-active').checked ? 1 : 0;
    
    try {
        const res = await fetch(API_URL + '/products/' + productId, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ stock, is_active: isActive })
        });
        
        const result = await res.json();
        
        if (result.success) {
            closeProductModal();
            await loadProducts();
        } else {
            alert(result.message || 'Erreur');
        }
    } catch (err) {
        alert('Erreur de connexion');
    }
}

async function deleteProduct(productId) {
    if (!confirm('Supprimer ce produit ?')) return;
    
    try {
        const res = await fetch(API_URL + '/products/' + productId, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const result = await res.json();
        
        if (result.success) {
            await Promise.all([loadProducts(), loadStats()]);
        } else {
            alert(result.message || 'Erreur');
        }
    } catch (err) {
        alert('Erreur de connexion');
    }
}

// ============ COMMANDES ============
async function updateOrderStatus(orderId, status) {
    try {
        const res = await fetch(API_URL + '/orders/' + orderId + '/status', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ status })
        });
        
        const result = await res.json();
        
        if (result.success) {
            await loadOrders();
        } else {
            alert('Erreur lors de la mise à jour');
        }
    } catch (err) {
        alert('Erreur de connexion');
    }
}

// ============ MESSAGES ============
async function loadMessages() {
    try {
        const res = await fetch(API_URL + '/messages', { credentials: 'include' });
        const messages = await res.json();
        const container = document.getElementById('messages-list');
        const badge = document.getElementById('msg-badge');
        
        const unreadCount = messages.filter(m => !m.is_read).length;
        if (unreadCount > 0) {
            badge.textContent = unreadCount;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
        
        if (messages.length === 0) {
            container.innerHTML = '<div style="text-align:center;color:#636e72;padding:50px 20px;"><i class="fas fa-inbox" style="font-size:48px;opacity:0.3;"></i><p style="margin-top:15px;">Aucun message</p></div>';
            return;
        }
        
        container.innerHTML = messages.map(m => `
            <div class="message-card ${m.is_read ? '' : 'unread'}">
                <div class="message-header">
                    <span class="message-user"><i class="fas fa-envelope"></i> ${m.subject}</span>
                    <span class="message-date"><i class="far fa-calendar-alt"></i> ${new Date(m.created_at).toLocaleDateString('fr-FR')}</span>
                </div>
                <div class="message-body">${m.message}</div>
                ${m.admin_reply ? `
                    <div class="message-reply">
                        <div class="message-reply-header"><i class="fas fa-reply"></i> Réponse de l'administrateur:</div>
                        <p>${m.admin_reply}</p>
                    </div>
                ` : '<p class="message-pending"><i class="fas fa-clock"></i> En attente de réponse...</p>'}
            </div>
        `).join('');
    } catch (err) {
        console.error('Messages error:', err);
    }
}

// Message form handler
document.addEventListener('DOMContentLoaded', () => {
    const msgForm = document.getElementById('message-form');
    if (msgForm) {
        msgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const subject = document.getElementById('message-subject').value.trim();
            const message = document.getElementById('message-text').value.trim();
            
            if (!subject || !message) {
                alert('Veuillez remplir tous les champs');
                return;
            }
            
            try {
                const res = await fetch(API_URL + '/messages', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ subject, message })
                });
                
                const result = await res.json();
                
                if (result.success) {
                    document.getElementById('message-subject').value = '';
                    document.getElementById('message-text').value = '';
                    await loadMessages();
                    alert('Message envoyé avec succès !');
                } else {
                    alert('Erreur: ' + (result.error || 'Impossible d\'envoyer le message'));
                }
            } catch (err) {
                alert('Erreur de connexion');
            }
        });
    }
});
