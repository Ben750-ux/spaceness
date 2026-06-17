"""
Vendor API - Flask REST API pour le dashboard boutique
"""
import sys
import os

# Ajouter le dossier parent au path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask, jsonify, request, session, send_file
from flask_cors import CORS
import database as db

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(BASE_DIR, 'vendor')

app = Flask(__name__)
app.secret_key = 'vendor-secret-key-12345'
CORS(app, supports_credentials=True)

@app.after_request
def add_no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


def check_vendor_auth():
    """Vérifie si le vendeur est authentifié"""
    return 'vendor_id' in session


def get_vendor_shop_id():
    """Récupère l'ID de la boutique du vendeur connecté"""
    vendor_id = session.get('vendor_id')
    if not vendor_id:
        return None
    shop = db.get_shop_by_owner(vendor_id)
    if not shop:
        return None
    return shop['id']


# ============ AUTHENTIFICATION ============
@app.route('/vendor_api/login', methods=['POST'])
def vendor_login():
    print("=== LOGIN ATTEMPT ===")
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    
    print(f"Email: {email}")
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email et mot de passe requis'})
    
    ok, msg, user = db.login_user(email, password)
    print(f"Login result: ok={ok}, msg={msg}, user={user}")
    
    if not ok:
        return jsonify({'success': False, 'error': msg})
    
    if user['role'] != 'boutique':
        print(f"User role is: {user['role']}")
        return jsonify({'success': False, 'error': 'Ce compte n\'est pas une boutique'})
    
    session['vendor_id'] = user['id']
    session['vendor_name'] = user['full_name']
    session['vendor_email'] = user['email']
    
    shop = db.get_shop_by_owner(user['id'])
    print(f"Shop: {shop}")
    
    return jsonify({
        'success': True,
        'vendor': {
            'id': user['id'],
            'name': user['full_name'],
            'email': user['email'],
            'shop_id': shop['id'] if shop else None,
            'shop_name': shop['shop_name'] if shop else None
        }
    })


@app.route('/vendor_api/logout', methods=['POST'])
def vendor_logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/vendor_api/check-auth', methods=['GET'])
def check_auth():
    if not check_vendor_auth():
        return jsonify({'authenticated': False})
    
    vendor_id = session.get('vendor_id')
    shop = db.get_shop_by_owner(vendor_id)
    
    return jsonify({
        'authenticated': True,
        'vendor': {
            'id': session.get('vendor_id'),
            'name': session.get('vendor_name'),
            'email': session.get('vendor_email'),
            'shop_id': shop['id'] if shop else None,
            'shop_name': shop['shop_name'] if shop else None
        }
    })


# ============ STATISTIQUES ============
@app.route('/vendor_api/stats', methods=['GET'])
def get_vendor_stats():
    shop_id = get_vendor_shop_id()
    if not shop_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    return jsonify({
        'total_products': db.count_shop_products(shop_id),
        'total_orders': db.count_shop_orders(shop_id),
        'total_revenue': db.get_shop_revenue(shop_id),
        'total_subscribers': db.get_shop_subscriber_count(shop_id),
    })


@app.route('/vendor_api/stats/monthly', methods=['GET'])
def get_vendor_monthly_stats():
    shop_id = get_vendor_shop_id()
    if not shop_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    monthly = db.get_shop_monthly_stats(shop_id)
    return jsonify([dict(m) for m in monthly])


# ============ BOUTIQUE ============
@app.route('/vendor_api/shop', methods=['GET'])
def get_vendor_shop():
    if not check_vendor_auth():
        return jsonify({'error': 'Non autorisé'}), 401
    
    vendor_id = session.get('vendor_id')
    shop = db.get_shop_by_owner(vendor_id)
    if not shop:
        return jsonify({'error': 'Boutique non trouvée'}), 404
    
    return jsonify(dict(shop))


@app.route('/vendor_api/shop', methods=['PUT'])
def update_vendor_shop():
    print("=== UPDATE SHOP ===")
    print("Session:", dict(session))
    
    if not check_vendor_auth():
        print("Non autorisé - vendor_id dans session:", 'vendor_id' in session)
        return jsonify({'success': False, 'error': 'Non autorisé'}), 401
    
    vendor_id = session.get('vendor_id')
    data = request.json
    print("Data:", data)
    
    ok, msg = db.update_shop(
        vendor_id,
        data.get('shop_name', ''),
        data.get('description', ''),
        data.get('contact_info', ''),
        data.get('logo_url', ''),
        data.get('banner_url', '')
    )
    print("Result:", ok, msg)
    return jsonify({'success': ok, 'message': msg})


# ============ PRODUITS ============
@app.route('/vendor_api/products', methods=['GET'])
def get_vendor_products():
    shop_id = get_vendor_shop_id()
    if not shop_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    products = db.list_shop_products(shop_id)
    return jsonify([dict(p) for p in products])


@app.route('/vendor_api/products', methods=['POST'])
def add_vendor_product():
    print("=== ADD PRODUCT ===")
    print("Session:", dict(session))
    
    if not check_vendor_auth():
        print("Non autorisé")
        return jsonify({'success': False, 'error': 'Non autorisé'}), 401
    
    vendor_id = session.get('vendor_id')
    data = request.json
    print("Data:", data)
    
    ok, msg = db.add_product(
        vendor_id,
        data.get('name', ''),
        data.get('category', 'General'),
        float(data.get('price', 0)),
        int(data.get('stock', 0)),
        data.get('description', ''),
        data.get('image_url', '')
    )
    print("Result:", ok, msg)
    return jsonify({'success': ok, 'message': msg})


@app.route('/vendor_api/products/<int:product_id>', methods=['PUT'])
def update_vendor_product(product_id):
    if not check_vendor_auth():
        return jsonify({'error': 'Non autorisé'}), 401
    
    vendor_id = session.get('vendor_id')
    data = request.json
    
    ok, msg = db.update_product_stock(
        product_id,
        vendor_id,
        int(data.get('stock', 0)),
        int(data.get('is_active', 1))
    )
    return jsonify({'success': ok, 'message': msg})


@app.route('/vendor_api/products/<int:product_id>', methods=['DELETE'])
def delete_vendor_product(product_id):
    if not check_vendor_auth():
        return jsonify({'error': 'Non autorisé'}), 401
    
    vendor_id = session.get('vendor_id')
    ok, msg = db.delete_product_by_owner(product_id, vendor_id)
    return jsonify({'success': ok, 'message': msg})


# ============ COMMANDES ============
@app.route('/vendor_api/orders', methods=['GET'])
def get_vendor_orders():
    shop_id = get_vendor_shop_id()
    if not shop_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    orders = db.list_shop_orders_anonymous(shop_id)
    return jsonify([dict(o) for o in orders])


@app.route('/vendor_api/orders/<int:order_id>/status', methods=['PUT'])
def update_vendor_order_status(order_id):
    if not check_vendor_auth():
        return jsonify({'error': 'Non autorisé'}), 401
    
    vendor_id = session.get('vendor_id')
    shop = db.get_shop_by_owner(vendor_id)
    if not shop:
        return jsonify({'error': 'Boutique non trouvée'}), 404
    
    data = request.json
    ok = db.update_order_status_if_shop(order_id, shop['id'], data.get('status', 'pending'))
    return jsonify({'success': ok})


# ============ MESSAGES ============
@app.route('/vendor_api/messages', methods=['GET'])
def get_vendor_messages():
    shop_id = get_vendor_shop_id()
    if not shop_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    messages = db.get_vendor_messages(shop_id)
    return jsonify([dict(m) for m in messages])


@app.route('/vendor_api/messages', methods=['POST'])
def send_vendor_message_api():
    shop_id = get_vendor_shop_id()
    if not shop_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    data = request.json
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    
    if not subject or not message:
        return jsonify({'success': False, 'error': 'Sujet et message requis'})
    
    ok = db.send_vendor_message(shop_id, subject, message)
    return jsonify({'success': ok})


# ============ PAGES WEB ============
@app.route('/')
def root():
    return send_file(os.path.join(VENDOR_DIR, 'index.html'))

@app.route('/vendor/')
def vendor_index():
    return send_file(os.path.join(VENDOR_DIR, 'index.html'))


@app.route('/vendor/<path:filename>')
def vendor_static(filename):
    file_path = os.path.join(VENDOR_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "File not found: " + filename, 404


if __name__ == '__main__':
    print("=" * 60)
    print("Dashboard Boutique Spaceness")
    print("=" * 60)
    print(f"Dossier vendor: {VENDOR_DIR}")
    print(f"Existe: {os.path.exists(VENDOR_DIR)}")
    if os.path.exists(VENDOR_DIR):
        print(f"Fichiers: {os.listdir(VENDOR_DIR)}")
    print("")
    print("Ouvrez: http://localhost:5001/vendor/")
    print("Ctrl+C pour arreter")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
