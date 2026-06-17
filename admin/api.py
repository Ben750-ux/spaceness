"""
Admin API - Flask REST API pour le dashboard administrateur
"""
import sys
import os
import sqlite3
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import database as db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__)
CORS(app)


# ============ STATISTIQUES ============
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retourne les statistiques générales"""
    stats = {
        'total_users': db.count_users(),
        'total_products': db.count_products(),
        'total_orders': db.count_orders(),
        'total_shops': db.count_shops(),
    }
    return jsonify(stats)


# ============ UTILISATEURS ============
@app.route('/api/users', methods=['GET'])
def get_users():
    """Liste tous les utilisateurs"""
    users = db.list_all_users()
    return jsonify([dict(u) for u in users])


@app.route('/api/users/<int:user_id>/block', methods=['POST'])
def block_user(user_id):
    """Bloquer ou débloquer un utilisateur"""
    data = request.json
    blocked = data.get('blocked', True)
    success = db.toggle_user_block(user_id, blocked)
    return jsonify({'success': success})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Supprimer un utilisateur"""
    success = db.delete_user(user_id)
    return jsonify({'success': success})


@app.route('/api/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """Récupère les commandes d'un utilisateur"""
    orders = db.get_user_orders(user_id)
    return jsonify([dict(o) for o in orders])


# ============ PRODUITS ============
@app.route('/api/products', methods=['GET'])
def get_products():
    """Liste tous les produits"""
    products = db.list_all_products()
    return jsonify([dict(p) for p in products])


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Supprimer un produit"""
    success = db.delete_product(product_id)
    return jsonify({'success': success})


# ============ BOUTIQUES ============
@app.route('/api/shops', methods=['GET'])
def get_shops():
    """Liste toutes les boutiques avec infos propriétaire"""
    with db._get_connection() as conn:
        shops = conn.execute("""
            SELECT s.*, u.full_name as owner_name, u.email as owner_email
            FROM shops s
            LEFT JOIN users u ON s.owner_user_id = u.id
            ORDER BY s.id DESC
        """).fetchall()
    return jsonify([dict(s) for s in shops])


@app.route('/api/shops/<int:shop_id>', methods=['DELETE'])
def delete_shop(shop_id):
    """Supprimer une boutique"""
    success = db.delete_shop(shop_id)
    return jsonify({'success': success})


# ============ COMMANDES ============
@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Liste toutes les commandes"""
    orders = db.list_all_orders()
    return jsonify([dict(o) for o in orders])


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Mettre à jour le statut d'une commande"""
    data = request.json
    status = data.get('status', 'pending')
    success = db.update_order_status(order_id, status)
    return jsonify({'success': success})


# ============ MESSAGES ============
@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Liste tous les messages"""
    messages = db.get_all_messages()
    return jsonify([dict(m) for m in messages])


@app.route('/api/messages/<int:message_id>/reply', methods=['POST'])
def reply_message(message_id):
    """Répond à un message"""
    data = request.json
    reply = data.get('reply', '')
    success = db.reply_to_message(message_id, reply)
    return jsonify({'success': success})


@app.route('/api/messages/<int:message_id>/read', methods=['PUT'])
def mark_read(message_id):
    """Marque un message comme lu"""
    success = db.mark_message_read(message_id)
    return jsonify({'success': success})


@app.route('/api/messages/unread/count', methods=['GET'])
def unread_count():
    """Compte les messages non lus"""
    count = db.count_unread_messages()
    return jsonify({'count': count})


@app.route('/api/messages/send', methods=['POST'])
def send_message():
    """Envoie un nouveau message à un utilisateur"""
    data = request.json
    user_id = data.get('user_id')
    subject = data.get('subject', '')
    message = data.get('message', '')
    if not user_id or not subject or not message:
        return jsonify({'success': False, 'error': 'Missing data'})
    success = db.send_admin_message(user_id, subject, message, is_from_admin=True)
    return jsonify({'success': success})


# ============ CRÉATION BOUTIQUE ============
@app.route('/api/shops/create', methods=['POST'])
def create_shop():
    """Crée une nouvelle boutique avec un compte vendeur"""
    data = request.json
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    shop_name = data.get('shop_name', '').strip()
    description = data.get('description', '').strip()
    contact_info = data.get('contact_info', '').strip()
    
    if not full_name or not email or not password or not shop_name:
        return jsonify({'success': False, 'error': 'Tous les champs obligatoires doivent être remplis'})
    
    if len(password) < 8:
        return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 8 caractères'})
    
    try:
        with db._get_connection() as conn:
            salt, pwd_hash = db._hash_password(password)
            cur = conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash, password_salt, role, created_at)
                VALUES (?, ?, ?, ?, 'boutique', ?)
                """,
                (full_name, email, pwd_hash, salt, datetime.utcnow().isoformat()),
            )
            owner_id = cur.lastrowid
            
            conn.execute(
                """
                INSERT INTO shops (owner_user_id, shop_name, description, contact_info)
                VALUES (?, ?, ?, ?)
                """,
                (owner_id, shop_name, description, contact_info),
            )
        
        return jsonify({
            'success': True,
            'message': 'Boutique créée avec succès',
            'credentials': {
                'email': email,
                'password': password
            }
        })
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Cet email est déjà utilisé'})


# ============ PARAMÈTRES APP ============
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Récupère les paramètres de l'app"""
    settings = db.get_app_settings()
    return jsonify(settings)


@app.route('/api/settings/block', methods=['PUT'])
def update_block():
    """Configure le blocage de l'app"""
    data = request.json
    is_blocked = data.get('is_blocked', False)
    block_message = data.get('block_message', '')
    success = db.set_app_blocked(is_blocked, block_message)
    return jsonify({'success': success})


# ============ ABONNEMENTS UTILISATEUR ============
@app.route('/api/users/<int:user_id>/subscriptions', methods=['GET'])
def get_user_subscriptions(user_id):
    """Récupère les boutiques auxquelles un utilisateur est abonné"""
    subscriptions = db.get_user_subscriptions(user_id)
    return jsonify([dict(s) for s in subscriptions])


# ============ MESSAGES BOUTIQUE <-> ADMIN ============
@app.route('/api/vendor-messages', methods=['GET'])
def get_all_vendor_messages():
    """Récupère tous les messages boutique <-> admin"""
    messages = db.get_all_vendor_admin_messages()
    return jsonify([dict(m) for m in messages])


@app.route('/api/vendor-messages/<int:message_id>/reply', methods=['POST'])
def reply_vendor_message(message_id):
    """Répond à un message de boutique"""
    data = request.json
    reply = data.get('reply', '')
    if not reply:
        return jsonify({'success': False, 'error': 'Réponse requise'})
    success = db.reply_vendor_message(message_id, reply)
    return jsonify({'success': success})


@app.route('/api/shops/list-all', methods=['GET'])
def get_all_shops():
    """Récupère toutes les boutiques pour l'admin"""
    shops = db.get_all_shops_for_admin()
    return jsonify([dict(s) for s in shops])


@app.route('/api/shops/<int:shop_id>/message', methods=['POST'])
def send_message_to_shop(shop_id):
    """Envoie un message à une boutique"""
    data = request.json
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    if not subject or not message:
        return jsonify({'success': False, 'error': 'Sujet et message requis'})
    success = db.send_message_to_shop(shop_id, subject, message)
    if success:
        db.log_activity(None, 'Admin', 'message_sent', f'Message envoyé à boutique #{shop_id}')
    return jsonify({'success': success})


# ============ JOURNAL D'ACTIVITÉ ============
@app.route('/api/activity-log', methods=['GET'])
def get_activity_log():
    """Récupère le journal d'activité"""
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_activity_log(limit)
    return jsonify([dict(l) for l in logs])


# ============ STATISTIQUES AVANCÉES ============
@app.route('/api/stats/advanced', methods=['GET'])
def get_advanced_stats():
    """Statistiques avancées"""
    days = request.args.get('days', 30, type=int)
    
    daily_orders = db.get_daily_orders_stats(days)
    popular_products = db.get_popular_products(10)
    monthly_stats = db.get_monthly_stats()
    
    return jsonify({
        'daily_orders': [dict(d) for d in daily_orders],
        'popular_products': [dict(p) for p in popular_products],
        'monthly_stats': [dict(m) for m in monthly_stats],
    })


# ============ CONVERSATIONS CLIENTS ============
@app.route('/api/conversations/clients', methods=['GET'])
def get_client_conversations():
    """Récupère les conversations clients (groupées par utilisateur)"""
    conversations = db.get_client_conversations()
    return jsonify(conversations)


@app.route('/api/conversations/clients/<int:user_id>', methods=['GET'])
def get_client_conversation(user_id):
    """Récupère les messages d'une conversation client"""
    messages = db.get_client_conversation(user_id)
    return jsonify([dict(m) for m in messages])


@app.route('/api/conversations/clients/<int:user_id>/read', methods=['PUT'])
def mark_client_conversation_read(user_id):
    """Marque une conversation client comme lue"""
    success = db.mark_client_conversation_read(user_id)
    return jsonify({'success': success})


@app.route('/api/conversations/clients/unread-count', methods=['GET'])
def get_unread_client_count():
    """Compte les conversations client non lues"""
    count = db.count_unread_client_conversations()
    return jsonify({'count': count})


# ============ CONVERSATIONS BOUTIQUES ============
@app.route('/api/conversations/shops', methods=['GET'])
def get_shop_conversations():
    """Récupère les conversations boutiques (groupées par boutique)"""
    conversations = db.get_shop_conversations()
    return jsonify(conversations)


@app.route('/api/conversations/shops/<int:shop_id>', methods=['GET'])
def get_shop_conversation(shop_id):
    """Récupère les messages d'une conversation boutique"""
    messages = db.get_shop_conversation(shop_id)
    return jsonify([dict(m) for m in messages])


@app.route('/api/conversations/shops/<int:shop_id>/read', methods=['PUT'])
def mark_shop_conversation_read(shop_id):
    """Marque une conversation boutique comme lue"""
    success = db.mark_shop_conversation_read(shop_id)
    return jsonify({'success': success})


@app.route('/api/conversations/shops/unread-count', methods=['GET'])
def get_unread_shop_count():
    """Compte les conversations boutique non lues"""
    count = db.count_unread_shop_conversations()
    return jsonify({'count': count})


# ============ GESTION BOUTIQUES ============
@app.route('/api/shops/<int:shop_id>/details', methods=['GET'])
def get_shop_details(shop_id):
    """Récupère les détails d'une boutique avec propriétaire"""
    shop = db.get_shop_with_owner(shop_id)
    if not shop:
        return jsonify({'error': 'Boutique introuvable'}), 404
    return jsonify(shop)


@app.route('/api/shops/<int:shop_id>/credentials', methods=['PUT'])
def update_shop_credentials(shop_id):
    """Modifie les identifiants d'une boutique"""
    data = request.json
    owner_name = data.get('owner_name')
    password = data.get('password')
    
    if password and len(password) < 8:
        return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 8 caractères'})
    
    success, message = db.update_shop_credentials(shop_id, owner_name, password)
    return jsonify({'success': success, 'message': message})


@app.route('/api/shops/<int:shop_id>/info', methods=['PUT'])
def update_shop_info(shop_id):
    """Modifie les informations d'une boutique"""
    data = request.json
    shop_name = data.get('shop_name')
    description = data.get('description')
    contact_info = data.get('contact_info')
    
    success, message = db.update_shop_info(shop_id, shop_name, description, contact_info)
    return jsonify({'success': success, 'message': message})


# ============ PAGE PRINCIPALE ============
@app.route('/')
def index():
    """Sert le dashboard HTML"""
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Sert les fichiers CSS et JS"""
    return send_from_directory(STATIC_DIR, filename)


if __name__ == '__main__':
    print("=" * 50)
    print("Dashboard Admin Spaceness")
    print("=" * 50)
    print("Ouvrez: http://localhost:5000")
    print("Ctrl+C pour arrêter")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
