let users = [], products = [], orders = [], shops = [], activityLogs = [];
let clientConversations = [], shopConversations = [];
let currentClientConversation = null, currentShopConversation = null;

document.addEventListener('DOMContentLoaded', function() {
    loadAllData();
    setupForms();
});

async function loadAllData() {
    try {
        const [statsRes, usersRes, productsRes, ordersRes, shopsRes, activityRes, clientConvRes, shopConvRes] = await Promise.all([
            fetch('/api/stats'),
            fetch('/api/users'),
            fetch('/api/products'),
            fetch('/api/orders'),
            fetch('/api/shops'),
            fetch('/api/activity-log'),
            fetch('/api/conversations/clients'),
            fetch('/api/conversations/shops')
        ]);

        const stats = await statsRes.json();
        document.getElementById('stat-users').textContent = stats.total_users || 0;
        document.getElementById('stat-products').textContent = stats.total_products || 0;
        document.getElementById('stat-orders').textContent = stats.total_orders || 0;
        document.getElementById('stat-shops').textContent = stats.total_shops || 0;

        users = await usersRes.json();
        products = await productsRes.json();
        orders = await ordersRes.json();
        shops = await shopsRes.json();
        activityLogs = await activityRes.json();
        clientConversations = await clientConvRes.json();
        shopConversations = await shopConvRes.json();

        renderUsers();
        renderProducts();
        renderOrders();
        renderShops();
        renderActivity();
        renderClientConversations();
        renderShopConversations();
        updateBadges();

    } catch (err) {
        console.error('Erreur chargement:', err);
    }
}

function updateBadges() {
    const unreadClients = clientConversations.filter(c => c.unread_client > 0).length;
    const unreadShops = shopConversations.filter(c => c.unread_admin > 0).length;
    document.getElementById('badge-clients').textContent = unreadClients;
    document.getElementById('badge-shops').textContent = unreadShops;
}

function renderUsers() {
    const tbody = document.getElementById('users-body');
    tbody.innerHTML = users.map(u => `
        <tr>
            <td>#${u.id}</td>
            <td><strong>${escapeHtml(u.full_name)}</strong></td>
            <td>${escapeHtml(u.email)}</td>
            <td><span class="badge badge-${u.role}">${u.role}</span></td>
            <td>${u.is_blocked ? '<span class="badge badge-danger">Bloqué</span>' : '<span class="badge badge-success">Actif</span>'}</td>
            <td>
                <button onclick="showUserDetails(${u.id})" class="btn-icon" title="Voir"><i class="fas fa-eye"></i></button>
                <button onclick="toggleBlock(${u.id}, ${!u.is_blocked})" class="btn-icon" title="${u.is_blocked ? 'Débloquer' : 'Bloquer'}">
                    <i class="fas fa-${u.is_blocked ? 'unlock' : 'lock'}"></i>
                </button>
                ${u.role !== 'admin' ? `<button onclick="deleteUser(${u.id})" class="btn-icon btn-danger" title="Supprimer"><i class="fas fa-trash"></i></button>` : ''}
            </td>
        </tr>
    `).join('');
}

function renderProducts() {
    const tbody = document.getElementById('products-body');
    tbody.innerHTML = products.map(p => `
        <tr>
            <td>#${p.id}</td>
            <td>${escapeHtml(p.name)}</td>
            <td>${escapeHtml(p.shop_name || '')}</td>
            <td>${(p.price || 0).toFixed(2)} €</td>
            <td>${p.stock}</td>
            <td>
                <button onclick="deleteProduct(${p.id})" class="btn-icon btn-danger" title="Supprimer"><i class="fas fa-trash"></i></button>
            </td>
        </tr>
    `).join('');
}

function renderOrders() {
    const tbody = document.getElementById('orders-body');
    tbody.innerHTML = orders.map(o => {
        const statusClass = { pending: 'badge-warning', confirmed: 'badge-info', shipped: 'badge-primary', delivered: 'badge-success', cancelled: 'badge-danger' }[o.status] || 'badge-secondary';
        return `
        <tr>
            <td>#${o.id}</td>
            <td>${escapeHtml(o.client_name || '')}</td>
            <td>${escapeHtml(o.product_name || '')}</td>
            <td>${o.quantity}</td>
            <td>${(o.total_amount || 0).toFixed(2)} €</td>
            <td><span class="badge ${statusClass}">${o.status}</span></td>
            <td>
                <select onchange="updateOrderStatus(${o.id}, this.value)" style="padding:5px;border-radius:5px;">
                    <option value="pending" ${o.status === 'pending' ? 'selected' : ''}>En attente</option>
                    <option value="confirmed" ${o.status === 'confirmed' ? 'selected' : ''}>Confirmée</option>
                    <option value="shipped" ${o.status === 'shipped' ? 'selected' : ''}>Expédiée</option>
                    <option value="delivered" ${o.status === 'delivered' ? 'selected' : ''}>Livrée</option>
                    <option value="cancelled" ${o.status === 'cancelled' ? 'selected' : ''}>Annulée</option>
                </select>
            </td>
        </tr>
    `}).join('');
}

function renderShops() {
    const tbody = document.getElementById('shops-body');
    tbody.innerHTML = shops.map(s => `
        <tr>
            <td>#${s.id}</td>
            <td><strong>${escapeHtml(s.shop_name)}</strong></td>
            <td>${escapeHtml(s.owner_name || s.description || '')}</td>
            <td>${escapeHtml(s.owner_email || s.contact_info || '')}</td>
            <td>
                <button onclick="openEditShopModal(${s.id})" class="btn-icon" title="Modifier"><i class="fas fa-edit"></i></button>
                <button onclick="deleteShop(${s.id})" class="btn-icon btn-danger" title="Supprimer"><i class="fas fa-trash"></i></button>
            </td>
        </tr>
    `).join('');
}

function renderActivity() {
    const container = document.getElementById('activity-list');
    if (activityLogs.length === 0) {
        container.innerHTML = '<p style="color:#999;text-align:center;padding:20px;">Aucune activité</p>';
        return;
    }
    container.innerHTML = activityLogs.map(log => `
        <div class="activity-item">
            <span class="activity-date">${formatDate(log.created_at)}</span>
            <strong>${escapeHtml(log.user_name || 'Système')}</strong>
            <span class="activity-action">${escapeHtml(log.action)}</span>
            <span class="activity-details">${escapeHtml(log.details || '')}</span>
        </div>
    `).join('');
}

function renderClientConversations() {
    const container = document.getElementById('clients-list');
    if (clientConversations.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;padding:30px;">Aucune conversation</p>';
        return;
    }
    container.innerHTML = clientConversations.map(c => `
        <div class="conversation-item ${currentClientConversation === c.user_id ? 'active' : ''}" 
             onclick="openClientConversation(${c.user_id})">
            <div class="conv-avatar">${getInitials(c.full_name)}</div>
            <div class="conv-info">
                <div class="conv-name">${escapeHtml(c.full_name)}</div>
                <div class="conv-preview">${escapeHtml(c.email)}</div>
                <div class="conv-meta">
                    <span>${formatDate(c.last_message_at)}</span>
                    ${c.unread_client > 0 ? `<span class="conv-unread">${c.unread_client}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

async function openClientConversation(userId) {
    currentClientConversation = userId;
    renderClientConversations();
    
    try {
        const res = await fetch(`/api/conversations/clients/${userId}`);
        const messages = await res.json();
        const conv = clientConversations.find(c => c.user_id === userId);
        
        await fetch(`/api/conversations/clients/${userId}/read`, { method: 'PUT' });
        
        const area = document.getElementById('client-conversation-area');
        area.innerHTML = `
            <div class="chat-header">
                <div class="conv-avatar">${getInitials(conv?.full_name || 'C')}</div>
                <div>
                    <h4>${escapeHtml(conv?.full_name || 'Client')}</h4>
                    <span>${escapeHtml(conv?.email || '')}</span>
                </div>
            </div>
            <div class="chat-messages" id="client-messages-list">
                ${messages.map(m => renderMessageBubble(m)).join('')}
            </div>
            <div class="chat-input">
                <textarea id="client-reply-input" placeholder="Écrire une réponse..." rows="2"></textarea>
                <div class="chat-input-row">
                    <button onclick="sendClientReply()" class="btn btn-success" style="flex:1;"><i class="fas fa-paper-plane"></i> Envoyer</button>
                </div>
            </div>
        `;
        
        setTimeout(() => {
            const msgList = document.getElementById('client-messages-list');
            if (msgList) msgList.scrollTop = msgList.scrollHeight;
        }, 100);
        
    } catch (err) {
        console.error('Erreur:', err);
    }
}

function renderMessageBubble(msg) {
    const isMine = msg.is_from_admin === 1;
    return `
        <div class="msg-bubble ${isMine ? 'msg-mine' : 'msg-theirs'}">
            ${!isMine ? `<div class="msg-subject">${escapeHtml(msg.subject)}</div>` : ''}
            <div>${escapeHtml(msg.message)}</div>
            ${msg.admin_reply ? `<div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(0,0,0,0.1);"><strong>Réponse admin:</strong> ${escapeHtml(msg.admin_reply)}</div>` : ''}
            <span class="msg-time">${formatDate(msg.created_at)}</span>
        </div>
    `;
}

async function sendClientReply() {
    if (!currentClientConversation) return;
    const input = document.getElementById('client-reply-input');
    const message = input.value.trim();
    if (!message) return;
    
    try {
        await fetch('/api/messages/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentClientConversation,
                subject: 'Réponse administration',
                message: message
            })
        });
        input.value = '';
        await openClientConversation(currentClientConversation);
        await loadAllData();
    } catch (err) {
        alert('Erreur lors de l\'envoi');
    }
}

function renderShopConversations() {
    const container = document.getElementById('shops-list');
    if (shopConversations.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;padding:30px;">Aucune conversation</p>';
        return;
    }
    container.innerHTML = shopConversations.map(c => `
        <div class="conversation-item ${currentShopConversation === c.shop_id ? 'active' : ''}" 
             onclick="openShopConversation(${c.shop_id})">
            <div class="conv-avatar" style="background:#00b894;"><i class="fas fa-store"></i></div>
            <div class="conv-info">
                <div class="conv-name">${escapeHtml(c.shop_name)}</div>
                <div class="conv-meta">
                    <span>${formatDate(c.last_message_at)}</span>
                    ${c.unread_admin > 0 ? `<span class="conv-unread">${c.unread_admin}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

async function openShopConversation(shopId) {
    currentShopConversation = shopId;
    renderShopConversations();
    
    try {
        const res = await fetch(`/api/conversations/shops/${shopId}`);
        const messages = await res.json();
        const conv = shopConversations.find(c => c.shop_id === shopId);
        
        await fetch(`/api/conversations/shops/${shopId}/read`, { method: 'PUT' });
        
        const area = document.getElementById('shop-conversation-area');
        area.innerHTML = `
            <div class="chat-header">
                <div class="conv-avatar" style="background:#00b894;"><i class="fas fa-store"></i></div>
                <div>
                    <h4>${escapeHtml(conv?.shop_name || 'Boutique')}</h4>
                    <span>#${shopId}</span>
                </div>
            </div>
            <div class="chat-messages" id="shop-messages-list">
                ${messages.map(m => renderShopMessageBubble(m)).join('')}
            </div>
            <div class="chat-input">
                <textarea id="shop-reply-input" placeholder="Répondre à la boutique..." rows="2"></textarea>
                <div class="chat-input-row">
                    <button onclick="sendShopReply()" class="btn btn-success" style="flex:1;"><i class="fas fa-paper-plane"></i> Envoyer</button>
                </div>
            </div>
        `;
        
        setTimeout(() => {
            const msgList = document.getElementById('shop-messages-list');
            if (msgList) msgList.scrollTop = msgList.scrollHeight;
        }, 100);
        
    } catch (err) {
        console.error('Erreur:', err);
    }
}

function renderShopMessageBubble(msg) {
    const isAdmin = msg.is_from_vendor === 0;
    return `
        <div class="msg-bubble ${isAdmin ? 'msg-mine' : 'msg-theirs'}">
            ${!isAdmin ? `<div class="msg-subject">${escapeHtml(msg.subject)}</div>` : ''}
            <div>${escapeHtml(msg.message)}</div>
            ${msg.admin_reply ? `<div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(0,0,0,0.1);"><strong>Réponse:</strong> ${escapeHtml(msg.admin_reply)}</div>` : ''}
            <span class="msg-time">${formatDate(msg.created_at)}</span>
        </div>
    `;
}

async function sendShopReply() {
    if (!currentShopConversation) return;
    const input = document.getElementById('shop-reply-input');
    const message = input.value.trim();
    if (!message) return;
    
    try {
        await fetch(`/api/shops/${currentShopConversation}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject: 'Réponse administration',
                message: message
            })
        });
        input.value = '';
        await openShopConversation(currentShopConversation);
        await loadAllData();
    } catch (err) {
        alert('Erreur lors de l\'envoi');
    }
}

async function openEditShopModal(shopId) {
    document.getElementById('edit-shop-id').value = shopId;
    document.getElementById('edit-shop-credentials-status').innerHTML = '';
    
    try {
        const res = await fetch(`/api/shops/${shopId}/details`);
        const shop = await res.json();
        
        document.getElementById('edit-shop-name').value = shop.shop_name || '';
        document.getElementById('edit-shop-desc').value = shop.description || '';
        document.getElementById('edit-shop-contact').value = shop.contact_info || '';
        document.getElementById('edit-owner-name').value = shop.owner_name || '';
        document.getElementById('edit-owner-password').value = '';
        
        document.getElementById('edit-shop-modal').style.display = 'flex';
    } catch (err) {
        alert('Erreur chargement boutique');
    }
}

function closeEditShopModal() {
    document.getElementById('edit-shop-modal').style.display = 'none';
}

async function saveShopInfo() {
    const shopId = document.getElementById('edit-shop-id').value;
    const data = {
        shop_name: document.getElementById('edit-shop-name').value,
        description: document.getElementById('edit-shop-desc').value,
        contact_info: document.getElementById('edit-shop-contact').value
    };
    
    try {
        const res = await fetch(`/api/shops/${shopId}/info`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) {
            alert('Boutique mise à jour!');
            await loadAllData();
        } else {
            alert('Erreur: ' + result.message);
        }
    } catch (err) {
        alert('Erreur');
    }
}

async function saveShopCredentials() {
    const shopId = document.getElementById('edit-shop-id').value;
    const ownerName = document.getElementById('edit-owner-name').value.trim();
    const password = document.getElementById('edit-owner-password').value;
    
    const statusEl = document.getElementById('edit-shop-credentials-status');
    
    if (password && password.length < 8) {
        statusEl.innerHTML = '<span style="color:red;">Le mot de passe doit contenir au moins 8 caractères</span>';
        return;
    }
    
    try {
        const res = await fetch(`/api/shops/${shopId}/credentials`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ owner_name: ownerName, password: password })
        });
        const result = await res.json();
        
        if (result.success) {
            statusEl.innerHTML = '<span style="color:green;"><i class="fas fa-check"></i> Identifiants mis à jour!</span>';
            document.getElementById('edit-owner-password').value = '';
        } else {
            statusEl.innerHTML = `<span style="color:red;"><i class="fas fa-times"></i> ${result.error}</span>`;
        }
    } catch (err) {
        statusEl.innerHTML = '<span style="color:red;">Erreur</span>';
    }
}

function openNewClientMsg() {
    const select = document.getElementById('new-msg-client');
    select.innerHTML = '<option value="">Sélectionner un client...</option>' + 
        users.filter(u => u.role === 'client').map(u => 
            `<option value="${u.id}">${escapeHtml(u.full_name)} (${escapeHtml(u.email)})</option>`
        ).join('');
    
    document.getElementById('new-msg-client-subject').value = '';
    document.getElementById('new-msg-client-text').value = '';
    document.getElementById('new-client-msg-modal').style.display = 'flex';
}

function closeNewClientMsg() {
    document.getElementById('new-client-msg-modal').style.display = 'none';
}

async function sendNewClientMessage() {
    const userId = document.getElementById('new-msg-client').value;
    const subject = document.getElementById('new-msg-client-subject').value.trim();
    const message = document.getElementById('new-msg-client-text').value.trim();
    
    if (!userId || !subject || !message) {
        alert('Tous les champs sont requis');
        return;
    }
    
    try {
        const res = await fetch('/api/messages/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: parseInt(userId), subject, message })
        });
        const result = await res.json();
        
        if (result.success) {
            closeNewClientMsg();
            await loadAllData();
            alert('Message envoyé!');
        }
    } catch (err) {
        alert('Erreur lors de l\'envoi');
    }
}

async function toggleBlock(userId, blocked) {
    try {
        await fetch(`/api/users/${userId}/block`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocked })
        });
        await loadAllData();
    } catch (err) {
        alert('Erreur');
    }
}

async function deleteUser(userId) {
    if (!confirm('Supprimer cet utilisateur?')) return;
    try {
        await fetch(`/api/users/${userId}`, { method: 'DELETE' });
        await loadAllData();
    } catch (err) {
        alert('Erreur');
    }
}

async function deleteProduct(productId) {
    if (!confirm('Supprimer ce produit?')) return;
    try {
        await fetch(`/api/products/${productId}`, { method: 'DELETE' });
        await loadAllData();
    } catch (err) {
        alert('Erreur');
    }
}

async function deleteShop(shopId) {
    if (!confirm('Supprimer cette boutique?')) return;
    try {
        await fetch(`/api/shops/${shopId}`, { method: 'DELETE' });
        await loadAllData();
    } catch (err) {
        alert('Erreur');
    }
}

async function updateOrderStatus(orderId, status) {
    try {
        await fetch(`/api/orders/${orderId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        await loadAllData();
    } catch (err) {
        alert('Erreur');
    }
}

async function showUserDetails(userId) {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    try {
        const res = await fetch(`/api/users/${userId}/orders`);
        const userOrders = await res.json();
        
        alert(`Nom: ${user.full_name}\nEmail: ${user.email}\nRôle: ${user.role}\nStatut: ${user.is_blocked ? 'Bloqué' : 'Actif'}\n\nCommandes: ${userOrders.length}`);
    } catch (err) {
        alert('Erreur chargement détails');
    }
}

function filterUsers(query) {
    query = query.toLowerCase();
    const filtered = users.filter(u => 
        u.full_name.toLowerCase().includes(query) || 
        u.email.toLowerCase().includes(query)
    );
    const tbody = document.getElementById('users-body');
    tbody.innerHTML = filtered.map(u => `
        <tr>
            <td>#${u.id}</td>
            <td><strong>${escapeHtml(u.full_name)}</strong></td>
            <td>${escapeHtml(u.email)}</td>
            <td><span class="badge badge-${u.role}">${u.role}</span></td>
            <td>${u.is_blocked ? '<span class="badge badge-danger">Bloqué</span>' : '<span class="badge badge-success">Actif</span>'}</td>
            <td>
                <button onclick="showUserDetails(${u.id})" class="btn-icon" title="Voir"><i class="fas fa-eye"></i></button>
                <button onclick="toggleBlock(${u.id}, ${!u.is_blocked})" class="btn-icon" title="${u.is_blocked ? 'Débloquer' : 'Bloquer'}">
                    <i class="fas fa-${u.is_blocked ? 'unlock' : 'lock'}"></i>
                </button>
                ${u.role !== 'admin' ? `<button onclick="deleteUser(${u.id})" class="btn-icon btn-danger" title="Supprimer"><i class="fas fa-trash"></i></button>` : ''}
            </td>
        </tr>
    `).join('');
}

function setupForms() {
    document.getElementById('create-shop-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const data = {
            full_name: document.getElementById('shop-owner-name').value,
            email: document.getElementById('shop-owner-email').value,
            password: document.getElementById('shop-owner-password').value,
            shop_name: document.getElementById('shop-new-name').value,
            description: document.getElementById('shop-new-description').value
        };
        
        const statusEl = document.getElementById('create-shop-status');
        statusEl.textContent = 'Création...';
        
        try {
            const res = await fetch('/api/shops/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            
            if (result.success) {
                statusEl.innerHTML = `<span style="color:green;"><i class="fas fa-check"></i> ${result.message}</span>`;
                statusEl.innerHTML += `<br><small style="color:#666;">Email: ${result.credentials.email}<br>Mot de passe: ${result.credentials.password}</small>`;
                this.reset();
                await loadAllData();
            } else {
                statusEl.innerHTML = `<span style="color:red;"><i class="fas fa-times"></i> ${result.error}</span>`;
            }
        } catch (err) {
            statusEl.innerHTML = '<span style="color:red;">Erreur</span>';
        }
    });
}

function showTab(tab) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    const section = document.getElementById('section-' + tab);
    if (section) section.classList.add('active');
    document.querySelectorAll(`[onclick*="showTab('${tab}')"]`).forEach(t => t.classList.add('active'));
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now - d;
    
    if (diff < 86400000 && d.getDate() === now.getDate()) {
        return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    }
    if (diff < 604800000) {
        return d.toLocaleDateString('fr-FR', { weekday: 'short', hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit' });
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
};
