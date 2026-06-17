import hashlib
import os
import random
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DB_NAME = "shop.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return salt, digest


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, digest = _hash_password(password, salt)
    return digest == password_hash


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('client', 'boutique', 'admin')),
                is_blocked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        # Ajout des colonnes de vérification email pour les utilisateurs existants
        verify_col_exists = any(
            c["name"] == "is_verified"
            for c in conn.execute("PRAGMA table_info(users)").fetchall()
        )
        _ensure_column_exists(conn, "users", "is_verified", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column_exists(conn, "users", "verification_code", "TEXT")
        _ensure_column_exists(conn, "users", "verification_code_expires", "TEXT")
        if not verify_col_exists:
            conn.execute("UPDATE users SET is_verified = 1")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id INTEGER NOT NULL UNIQUE,
                shop_name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                contact_info TEXT NOT NULL DEFAULT '',
                logo_url TEXT NOT NULL DEFAULT '',
                banner_url TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(owner_user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        _ensure_column_exists(conn, "shops", "logo_url", "TEXT NOT NULL DEFAULT ''")
        _ensure_column_exists(conn, "shops", "banner_url", "TEXT NOT NULL DEFAULT ''")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                description TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                image_url_2 TEXT NOT NULL DEFAULT '',
                image_url_3 TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(shop_id) REFERENCES shops(id) ON DELETE CASCADE
            )
            """
        )
        _ensure_column_exists(conn, "products", "image_url", "TEXT NOT NULL DEFAULT ''")
        _ensure_column_exists(conn, "products", "image_url_2", "TEXT NOT NULL DEFAULT ''")
        _ensure_column_exists(conn, "products", "image_url_3", "TEXT NOT NULL DEFAULT ''")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                total_amount REAL NOT NULL CHECK(total_amount >= 0),
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                FOREIGN KEY(client_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_products_shop_id ON products(shop_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_user_id)"
        )
        # Table pour les abonnements aux boutiques
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shop_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_user_id INTEGER NOT NULL,
                shop_id INTEGER NOT NULL,
                subscribed_at TEXT NOT NULL,
                FOREIGN KEY(client_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(shop_id) REFERENCES shops(id) ON DELETE CASCADE,
                UNIQUE(client_user_id, shop_id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_client ON shop_subscriptions(client_user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_shop ON shop_subscriptions(shop_id)"
        )
        # Table pour les favoris
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE(user_id, product_id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)"
        )
        # Table pour l'historique de navigation
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS view_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                viewed_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_user ON view_history(user_id)"
        )
        # Table pour les avis/ratings
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE(user_id, product_id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_product ON product_reviews(product_id)"
        )
        # Table pour les messages admin
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                admin_reply TEXT,
                replied_at TEXT,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                is_from_admin INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_user ON admin_messages(user_id)"
        )
        _ensure_column_exists(conn, "admin_messages", "is_from_admin", "INTEGER NOT NULL DEFAULT 0")
        # Table pour les paramètres de l'app
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                block_message TEXT NOT NULL DEFAULT ''
            )
            """
        )
        # Insert default settings if not exists
        existing = conn.execute("SELECT id FROM app_settings WHERE id = 1").fetchone()
        if not existing:
            conn.execute("INSERT INTO app_settings (id, is_blocked, block_message) VALUES (1, 0, '')")
        
        # Table pour les messages boutique <-> admin
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vendor_admin_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id INTEGER NOT NULL,
                vendor_user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                admin_reply TEXT,
                replied_at TEXT,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                is_from_vendor INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(shop_id) REFERENCES shops(id) ON DELETE CASCADE,
                FOREIGN KEY(vendor_user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_vendor_messages_shop ON vendor_admin_messages(shop_id)"
        )
        
        # Table pour les tentatives de connexion
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                attempted_at TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email)"
        )
        
        # Table pour le journal d'activité admin
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log(user_id)"
        )
        
        _seed_admin(conn)
        _seed_demo_data(conn)


def _seed_admin(conn: sqlite3.Connection) -> None:
    exists = conn.execute(
        "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
    ).fetchone()
    if exists:
        return
    salt, pwd_hash = _hash_password("admin123")
    conn.execute(
        """
        INSERT INTO users (full_name, email, password_hash, password_salt, role, created_at)
        VALUES (?, ?, ?, ?, 'admin', ?)
        """,
        ("Super Admin", "admin@shop.local", pwd_hash, salt, datetime.utcnow().isoformat()),
    )


def _seed_demo_data(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS c FROM shops").fetchone()["c"]
    if count > 0:
        return

    vendors = [
        (
            "Boutique Tech",
            "tech@shop.local",
            "Boutique d'accessoires tech premium.",
            "contact@techshop.local",
            "https://picsum.photos/seed/techlogo/240/240",
            "https://picsum.photos/seed/techbanner/1200/500",
        ),
        (
            "Maison Mode",
            "mode@shop.local",
            "Mode chic et elegante pour tous les styles.",
            "contact@maisonmode.local",
            "https://picsum.photos/seed/modelogo/240/240",
            "https://picsum.photos/seed/modebanner/1200/500",
        ),
    ]
    for shop_name, email, desc, contact, logo_url, banner_url in vendors:
        salt, pwd_hash = _hash_password("vendor123")
        cur = conn.execute(
            """
            INSERT INTO users (full_name, email, password_hash, password_salt, role, created_at)
            VALUES (?, ?, ?, ?, 'boutique', ?)
            """,
            (shop_name, email, pwd_hash, salt, datetime.utcnow().isoformat()),
        )
        owner_id = cur.lastrowid
        shop_cur = conn.execute(
            """
            INSERT INTO shops (owner_user_id, shop_name, description, contact_info, logo_url, banner_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (owner_id, shop_name, desc, contact, logo_url, banner_url),
        )
        shop_id = shop_cur.lastrowid
        if shop_name == "Boutique Tech":
            products = [
                (
                    "Ecouteurs Bluetooth",
                    "Tech",
                    29.99,
                    20,
                    "Son clair et autonomie elevee.",
                    "https://picsum.photos/seed/ecouteurs/600/420",
                ),
                (
                    "Chargeur Rapide",
                    "Tech",
                    14.50,
                    30,
                    "Compatible USB-C.",
                    "https://picsum.photos/seed/chargeur/600/420",
                ),
            ]
        else:
            products = [
                (
                    "T-shirt Premium",
                    "Mode",
                    18.00,
                    50,
                    "Confortable et durable.",
                    "https://picsum.photos/seed/tshirt/600/420",
                ),
                (
                    "Jean Slim",
                    "Mode",
                    35.00,
                    25,
                    "Style moderne.",
                    "https://picsum.photos/seed/jean/600/420",
                ),
            ]
        for p in products:
            conn.execute(
                """
                INSERT INTO products (shop_id, name, category, price, stock, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (shop_id, *p),
            )


def create_user(full_name: str, email: str, password: str, role: str) -> Tuple[bool, str]:
    if role not in {"client", "boutique"}:
        return False, "Role invalide."
    if len(password) < 6:
        return False, "Le mot de passe doit avoir au moins 6 caracteres."
    try:
        with _get_connection() as conn:
            salt, pwd_hash = _hash_password(password)
            cur = conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash, password_salt, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (full_name.strip(), email.strip().lower(), pwd_hash, salt, role, datetime.utcnow().isoformat()),
            )
            user_id = cur.lastrowid
            if role == "boutique":
                shop_name = f"{full_name.strip()} Shop"
                conn.execute(
                    """
                    INSERT INTO shops (owner_user_id, shop_name, description, contact_info)
                    VALUES (?, ?, '', '')
                    """,
                    (user_id, shop_name),
                )
        return True, "Compte cree avec succes."
    except sqlite3.IntegrityError:
        return False, "Cet email est deja utilise."


def login_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, full_name, email, password_hash, password_salt, role, is_blocked, is_verified
            FROM users WHERE email = ?
            """,
            (email.strip().lower(),),
        ).fetchone()
        if not row:
            return False, "Email ou mot de passe incorrect.", None
        if row["is_blocked"]:
            return False, "Compte bloque par l'administration.", None
        if not verify_password(password, row["password_salt"], row["password_hash"]):
            return False, "Email ou mot de passe incorrect.", None
        if not row["is_verified"]:
            return False, "VERIFICATION_REQUIRED", {"id": row["id"], "email": row["email"], "full_name": row["full_name"]}
        user = {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
        }
        return True, "Connexion reussie.", user


# ============ VÉRIFICATION EMAIL ============
def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))


def save_verification_code(user_id: int, code: str) -> None:
    expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    with _get_connection() as conn:
        conn.execute(
            "UPDATE users SET verification_code = ?, verification_code_expires = ? WHERE id = ?",
            (code, expires, user_id),
        )
        conn.commit()


def verify_email_code(user_id: int, code: str) -> Tuple[bool, str]:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT verification_code, verification_code_expires FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return False, "Utilisateur introuvable."
        if not row["verification_code"]:
            return False, "Aucun code de verification trouve."
        if row["verification_code"] != code:
            return False, "Code incorrect."
        expires = datetime.fromisoformat(row["verification_code_expires"])
        if datetime.utcnow() > expires:
            return False, "Code expire. Demandez un nouveau code."
        conn.execute(
            "UPDATE users SET is_verified = 1, verification_code = NULL, verification_code_expires = NULL WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        return True, "Email verifie avec succes !"


def is_user_verified(user_id: int) -> bool:
    with _get_connection() as conn:
        row = conn.execute("SELECT is_verified FROM users WHERE id = ?", (user_id,)).fetchone()
        return bool(row and row["is_verified"])


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, full_name, email, role, is_blocked, is_verified
            FROM users WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        if not row or row["is_blocked"]:
            return None
        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
            "is_verified": bool(row["is_verified"]),
        }


def get_shop_by_owner(owner_user_id: int) -> Optional[sqlite3.Row]:
    with _get_connection() as conn:
        return conn.execute(
            "SELECT * FROM shops WHERE owner_user_id = ?",
            (owner_user_id,),
        ).fetchone()


def update_shop(
    owner_user_id: int,
    shop_name: str,
    description: str,
    contact_info: str,
    logo_url: str,
    banner_url: str,
) -> Tuple[bool, str]:
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                UPDATE shops
                SET shop_name = ?, description = ?, contact_info = ?, logo_url = ?, banner_url = ?
                WHERE owner_user_id = ?
                """,
                (
                    shop_name.strip(),
                    description.strip(),
                    contact_info.strip(),
                    logo_url.strip(),
                    banner_url.strip(),
                    owner_user_id,
                ),
            )
        return True, "Profil boutique mis a jour."
    except sqlite3.IntegrityError:
        return False, "Nom de boutique deja utilise."


def add_product(
    owner_user_id: int,
    name: str,
    category: str,
    price: float,
    stock: int,
    description: str,
    image_url: str,
) -> Tuple[bool, str]:
    shop = get_shop_by_owner(owner_user_id)
    if not shop:
        return False, "Boutique introuvable."
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO products (shop_id, name, category, price, stock, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shop["id"],
                name.strip(),
                category.strip() or "General",
                price,
                stock,
                description.strip(),
                image_url.strip(),
            ),
        )
    return True, "Produit ajoute."


def update_product_stock(product_id: int, owner_user_id: int, stock: int, is_active: int) -> Tuple[bool, str]:
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.id
            FROM products p
            JOIN shops s ON s.id = p.shop_id
            WHERE p.id = ? AND s.owner_user_id = ?
            """,
            (product_id, owner_user_id),
        ).fetchone()
        if not row:
            return False, "Produit introuvable."
        conn.execute(
            "UPDATE products SET stock = ?, is_active = ? WHERE id = ?",
            (stock, is_active, product_id),
        )
    return True, "Produit mis a jour."


def list_shop_products(shop_id: int) -> List[sqlite3.Row]:
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT id, name, category, price, stock, description, image_url, image_url_2, image_url_3, is_active
            FROM products
            WHERE shop_id = ?
            ORDER BY id DESC
            """,
            (shop_id,),
        ).fetchall()


def list_market_products(search: str = "", category: str = "") -> List[sqlite3.Row]:
    search = search.strip().lower()
    category = category.strip().lower()
    base = """
        SELECT
            p.id, p.name, p.category, p.price, p.stock, p.description,
            p.image_url, p.image_url_2, p.image_url_3,
            s.id AS shop_id, s.shop_name
        FROM products p
        JOIN shops s ON s.id = p.shop_id
        WHERE p.is_active = 1 AND p.stock > 0
    """
    params: List[Any] = []
    if search:
        base += " AND (LOWER(p.name) LIKE ? OR LOWER(s.shop_name) LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    if category:
        base += " AND LOWER(p.category) = ?"
        params.append(category)
    base += " ORDER BY p.id DESC"
    with _get_connection() as conn:
        return conn.execute(base, tuple(params)).fetchall()


def get_product_by_id(product_id: int) -> Optional[sqlite3.Row]:
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT
                p.id, p.name, p.category, p.price, p.stock, p.description, 
                p.image_url, p.image_url_2, p.image_url_3, p.is_active,
                s.id AS shop_id, s.shop_name
            FROM products p
            JOIN shops s ON s.id = p.shop_id
            WHERE p.id = ?
            """,
            (product_id,),
        ).fetchone()


def _ensure_column_exists(
    conn: sqlite3.Connection, table_name: str, column_name: str, column_def: str
) -> None:
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    names = {c["name"] for c in cols}
    if column_name not in names:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


def get_shop_details(shop_id: int) -> Optional[sqlite3.Row]:
    with _get_connection() as conn:
        return conn.execute("SELECT * FROM shops WHERE id = ?", (shop_id,)).fetchone()


def place_order(client_user_id: int, product_id: int, quantity: int) -> Tuple[bool, str]:
    with _get_connection() as conn:
        product = conn.execute(
            "SELECT id, name, stock, price, is_active FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if not product:
            return False, "Produit introuvable."
        if not product["is_active"] or product["stock"] <= 0:
            return False, "Produit indisponible."
        if quantity <= 0:
            return False, "Quantite invalide."
        if product["stock"] < quantity:
            return False, "Stock insuffisant."

        total = float(product["price"]) * quantity
        conn.execute(
            """
            INSERT INTO orders (client_user_id, product_id, quantity, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (client_user_id, product_id, quantity, total, datetime.utcnow().isoformat()),
        )
        conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (quantity, product_id),
        )
    return True, "Commande enregistree."


def list_all_users() -> List[sqlite3.Row]:
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT id, full_name, email, role, is_blocked, created_at
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()


def set_user_block_status(user_id: int, blocked: int) -> Tuple[bool, str]:
    with _get_connection() as conn:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "Utilisateur introuvable."
        if row["role"] == "admin":
            return False, "Impossible de bloquer un administrateur."
        conn.execute("UPDATE users SET is_blocked = ? WHERE id = ?", (blocked, user_id))
    return True, "Statut utilisateur mis a jour."


def delete_user(user_id: int) -> Tuple[bool, str]:
    with _get_connection() as conn:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "Utilisateur introuvable."
        if row["role"] == "admin":
            return False, "Suppression d'admin non autorisee."
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return True, "Utilisateur supprime."


def create_vendor_account(full_name: str, email: str, password: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    if password is None or not password.strip():
        password = secrets.token_urlsafe(8)
    if len(password) < 8:
        return False, "Mot de passe vendeur trop court (8+).", None
    try:
        with _get_connection() as conn:
            salt, pwd_hash = _hash_password(password)
            cur = conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash, password_salt, role, created_at)
                VALUES (?, ?, ?, ?, 'boutique', ?)
                """,
                (full_name.strip(), email.strip().lower(), pwd_hash, salt, datetime.utcnow().isoformat()),
            )
            owner_id = cur.lastrowid
            shop_name = f"{full_name.strip()} Shop"
            conn.execute(
                """
                INSERT INTO shops (owner_user_id, shop_name, description, contact_info)
                VALUES (?, ?, '', '')
                """,
                (owner_id, shop_name),
            )
        return True, "Compte vendeur cree.", password
    except sqlite3.IntegrityError:
        return False, "Email vendeur deja utilise.", None


def list_orders_for_client(client_user_id: int) -> List[sqlite3.Row]:
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT
                o.id, o.quantity, o.total_amount, o.status, o.created_at,
                p.id AS product_id, p.name AS product_name, p.description AS product_description,
                p.price AS product_price,
                p.image_url AS product_image_url, p.image_url_2 AS product_image_url_2, 
                p.image_url_3 AS product_image_url_3, p.category AS product_category,
                s.id AS shop_id, s.shop_name, s.logo_url AS shop_logo_url
            FROM orders o
            JOIN products p ON p.id = o.product_id
            JOIN shops s ON s.id = p.shop_id
            WHERE o.client_user_id = ?
            ORDER BY o.id DESC
            """,
            (client_user_id,),
        ).fetchall()


def is_subscribed_to_shop(client_user_id: int, shop_id: int) -> bool:
    """Vérifie si un client est abonné à une boutique"""
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT id FROM shop_subscriptions WHERE client_user_id = ? AND shop_id = ?",
            (client_user_id, shop_id),
        ).fetchone()
        return result is not None


def subscribe_to_shop(client_user_id: int, shop_id: int) -> bool:
    """Abonne un client à une boutique"""
    with _get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO shop_subscriptions (client_user_id, shop_id, subscribed_at) VALUES (?, ?, ?)",
                (client_user_id, shop_id, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def add_to_favorites(user_id: int, product_id: int) -> bool:
    """Ajoute un produit aux favoris"""
    with _get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO favorites (user_id, product_id, created_at) VALUES (?, ?, ?)",
                (user_id, product_id, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def remove_from_favorites(user_id: int, product_id: int) -> bool:
    """Retire un produit des favoris"""
    with _get_connection() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        conn.commit()
        return True


def is_favorite(user_id: int, product_id: int) -> bool:
    """Vérifie si un produit est en favori"""
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        return result is not None


def list_favorites(user_id: int) -> List[sqlite3.Row]:
    """Liste les favoris d'un utilisateur"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT p.id, p.name, p.category, p.price, p.stock, p.description,
                p.image_url, p.image_url_2, p.image_url_3,
                s.id AS shop_id, s.shop_name, f.created_at AS favorited_at
            FROM favorites f
            JOIN products p ON p.id = f.product_id
            JOIN shops s ON s.id = p.shop_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            """,
            (user_id,),
        ).fetchall()


def add_to_history(user_id: int, product_id: int) -> None:
    """Ajoute un produit à l'historique de navigation"""
    with _get_connection() as conn:
        conn.execute(
            "DELETE FROM view_history WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        conn.execute(
            "INSERT INTO view_history (user_id, product_id, viewed_at) VALUES (?, ?, ?)",
            (user_id, product_id, datetime.utcnow().isoformat()),
        )
        conn.execute(
            """
            DELETE FROM view_history WHERE user_id = ? AND id NOT IN (
                SELECT id FROM view_history WHERE user_id = ? ORDER BY viewed_at DESC LIMIT 50
            )
            """,
            (user_id, user_id),
        )
        conn.commit()


def list_history(user_id: int, limit: int = 20) -> List[sqlite3.Row]:
    """Liste l'historique de navigation"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT p.id, p.name, p.category, p.price, p.stock, p.description,
                p.image_url, p.image_url_2, p.image_url_3,
                s.id AS shop_id, s.shop_name, h.viewed_at
            FROM view_history h
            JOIN products p ON p.id = h.product_id
            JOIN shops s ON s.id = p.shop_id
            WHERE h.user_id = ?
            ORDER BY h.viewed_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()


def clear_history(user_id: int) -> None:
    """Efface l'historique de navigation"""
    with _get_connection() as conn:
        conn.execute("DELETE FROM view_history WHERE user_id = ?", (user_id,))
        conn.commit()


def add_review(user_id: int, product_id: int, rating: int, comment: str = "") -> bool:
    """Ajoute ou modifie un avis"""
    if not 1 <= rating <= 5:
        return False
    with _get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO product_reviews (user_id, product_id, rating, comment, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, product_id, rating, comment, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.execute(
                """
                UPDATE product_reviews SET rating = ?, comment = ?, created_at = ?
                WHERE user_id = ? AND product_id = ?
                """,
                (rating, comment, datetime.utcnow().isoformat(), user_id, product_id),
            )
            conn.commit()
            return True


def get_product_reviews(product_id: int) -> List[sqlite3.Row]:
    """Liste les avis d'un produit"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT r.*, u.full_name AS user_name
            FROM product_reviews r
            JOIN users u ON u.id = r.user_id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
            """,
            (product_id,),
        ).fetchall()


def get_product_rating(product_id: int) -> Tuple[float, int]:
    """Retourne la note moyenne et le nombre d'avis"""
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM product_reviews WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        avg = result["avg_rating"] if result["avg_rating"] else 0.0
        count = result["count"] or 0
        return (round(avg, 1), count)


def get_user_review(user_id: int, product_id: int) -> Optional[sqlite3.Row]:
    """Retourne l'avis d'un utilisateur pour un produit"""
    with _get_connection() as conn:
        return conn.execute(
            "SELECT * FROM product_reviews WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()


def unsubscribe_from_shop(client_user_id: int, shop_id: int) -> bool:
    """Désabonne un client d'une boutique"""
    with _get_connection() as conn:
        conn.execute(
            "DELETE FROM shop_subscriptions WHERE client_user_id = ? AND shop_id = ?",
            (client_user_id, shop_id),
        )
        conn.commit()
        return True


def get_shop_subscriber_count(shop_id: int) -> int:
    """Récupère le nombre d'abonnés d'une boutique"""
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT COUNT(*) FROM shop_subscriptions WHERE shop_id = ?",
            (shop_id,),
        ).fetchone()
        return result[0] if result else 0


def list_subscribed_shops(client_user_id: int) -> List[sqlite3.Row]:
    """Liste toutes les boutiques auxquelles un client est abonné"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT s.id, s.shop_name, s.logo_url, s.description, s.subscribed_at
            FROM shops s
            JOIN shop_subscriptions sub ON s.id = sub.shop_id
            WHERE sub.client_user_id = ?
            ORDER BY sub.subscribed_at DESC
            """,
            (client_user_id,),
        ).fetchall()


def get_subscribed_shop_products(client_user_id: int) -> List[sqlite3.Row]:
    """Récupère les produits des boutiques auxquelles le client est abonné (pour affichage prioritaire)"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT p.*, s.shop_name, s.logo_url AS shop_logo_url, 1 AS is_subscribed
            FROM products p
            JOIN shops s ON p.shop_id = s.id
            JOIN shop_subscriptions sub ON s.id = sub.shop_id
            WHERE sub.client_user_id = ? AND p.is_active = 1
            ORDER BY p.id DESC
            """,
            (client_user_id,),
        ).fetchall()


# ============ FONCTIONS ADMIN ============
def count_users() -> int:
    """Compte le nombre total d'utilisateurs"""
    with _get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return result[0] if result else 0


def count_products() -> int:
    """Compte le nombre total de produits"""
    with _get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM products").fetchone()
        return result[0] if result else 0


def count_orders() -> int:
    """Compte le nombre total de commandes"""
    with _get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
        return result[0] if result else 0


def count_shops() -> int:
    """Compte le nombre total de boutiques"""
    with _get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM shops").fetchone()
        return result[0] if result else 0


def list_all_products() -> List[sqlite3.Row]:
    """Liste tous les produits avec infos boutique"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT p.*, s.shop_name 
            FROM products p
            JOIN shops s ON p.shop_id = s.id
            ORDER BY p.id DESC
            """
        ).fetchall()


def list_all_shops() -> List[sqlite3.Row]:
    """Liste toutes les boutiques"""
    with _get_connection() as conn:
        return conn.execute("SELECT * FROM shops ORDER BY id DESC").fetchall()


def list_all_orders() -> List[sqlite3.Row]:
    """Liste toutes les commandes avec détails"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT o.*, p.name as product_name, u.full_name as client_name, s.shop_name
            FROM orders o
            JOIN products p ON o.product_id = p.id
            JOIN users u ON o.client_user_id = u.id
            JOIN shops s ON p.shop_id = s.id
            ORDER BY o.id DESC
            """
        ).fetchall()


def toggle_user_block(user_id: int, blocked: bool) -> bool:
    """Active ou désactive le blocage d'un utilisateur"""
    try:
        with _get_connection() as conn:
            conn.execute("UPDATE users SET is_blocked = ? WHERE id = ?", (1 if blocked else 0, user_id))
        return True
    except Exception:
        return False


def delete_product(product_id: int) -> bool:
    """Supprime un produit"""
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return True
    except Exception:
        return False


def delete_shop(shop_id: int) -> bool:
    """Supprime une boutique"""
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM shops WHERE id = ?", (shop_id,))
        return True
    except Exception:
        return False


# ============ MESSAGES ADMIN ============
def send_admin_message(user_id: int, subject: str, message: str, is_from_admin: bool = False) -> bool:
    """Envoie un message (par user ou admin)"""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO admin_messages (user_id, subject, message, created_at, is_from_admin)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, subject, message, datetime.utcnow().isoformat(), 1 if is_from_admin else 0)
            )
        return True
    except Exception:
        return False


def get_user_messages(user_id: int) -> List[sqlite3.Row]:
    """Récupère les messages d'un utilisateur"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM admin_messages WHERE user_id = ? ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()


def get_all_messages() -> List[sqlite3.Row]:
    """Récupère tous les messages (pour admin)"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT m.*, u.full_name, u.email 
            FROM admin_messages m
            JOIN users u ON m.user_id = u.id
            ORDER BY m.created_at DESC
            """
        ).fetchall()


def reply_to_message(message_id: int, reply: str) -> bool:
    """Répond à un message"""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                UPDATE admin_messages 
                SET admin_reply = ?, replied_at = ?, is_read = 0
                WHERE id = ?
                """,
                (reply, datetime.utcnow().isoformat(), message_id)
            )
        return True
    except Exception:
        return False


def mark_message_read(message_id: int) -> bool:
    """Marque un message comme lu"""
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE admin_messages SET is_read = 1 WHERE id = ?",
                (message_id,)
            )
        return True
    except Exception:
        return False


def count_unread_messages() -> int:
    """Compte les messages non lus"""
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT COUNT(*) FROM admin_messages WHERE is_read = 0"
        ).fetchone()
        return result[0] if result else 0


def update_order_status(order_id: int, status: str) -> bool:
    """Met à jour le statut d'une commande"""
    try:
        with _get_connection() as conn:
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        return True
    except Exception:
        return False


def get_user_orders(user_id: int) -> List[sqlite3.Row]:
    """Récupère les commandes d'un utilisateur"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT o.*, p.name as product_name
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.client_user_id = ?
            ORDER BY o.id DESC
            """,
            (user_id,)
        ).fetchall()


def get_app_settings() -> Dict[str, Any]:
    """Récupère les paramètres de l'app"""
    with _get_connection() as conn:
        row = conn.execute("SELECT is_blocked, block_message FROM app_settings WHERE id = 1").fetchone()
        if row:
            return {"is_blocked": bool(row[0]), "block_message": row[1]}
        return {"is_blocked": False, "block_message": ""}


def set_app_blocked(is_blocked: bool, block_message: str) -> bool:
    """Configure le blocage de l'app"""
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE app_settings SET is_blocked = ?, block_message = ? WHERE id = 1",
                (1 if is_blocked else 0, block_message)
            )
        return True
    except Exception:
        return False


def get_user_subscriptions(user_id: int) -> List[sqlite3.Row]:
    """Récupère les boutiques auxquelles un utilisateur est abonné"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT s.* FROM shops s
            JOIN shop_subscriptions sub ON s.id = sub.shop_id
            WHERE sub.client_user_id = ?
            ORDER BY sub.subscribed_at DESC
            """,
            (user_id,)
        ).fetchall()


# ============ FONCTIONS BOUTIQUE ============
def count_shop_products(shop_id: int) -> int:
    """Compte les produits d'une boutique"""
    with _get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM products WHERE shop_id = ?", (shop_id,)).fetchone()
        return result[0] if result else 0


def count_shop_orders(shop_id: int) -> int:
    """Compte les commandes d'une boutique"""
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT COUNT(*) FROM orders o JOIN products p ON o.product_id = p.id WHERE p.shop_id = ?",
            (shop_id,)
        ).fetchone()
        return result[0] if result else 0


def get_shop_revenue(shop_id: int) -> float:
    """Calcule le revenu total d'une boutique"""
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT COALESCE(SUM(o.total_amount), 0) FROM orders o JOIN products p ON o.product_id = p.id WHERE p.shop_id = ?",
            (shop_id,)
        ).fetchone()
        return float(result[0]) if result else 0.0


def list_shop_orders(shop_id: int) -> List[sqlite3.Row]:
    """Liste les commandes d'une boutique"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT o.*, p.name as product_name, p.image_url as product_image,
                   u.full_name as client_name, u.email as client_email
            FROM orders o
            JOIN products p ON o.product_id = p.id
            JOIN users u ON o.client_user_id = u.id
            WHERE p.shop_id = ?
            ORDER BY o.id DESC
            """,
            (shop_id,)
        ).fetchall()


def delete_product_by_owner(product_id: int, owner_user_id: int) -> Tuple[bool, str]:
    """Supprime un produit (uniquement si appartient à la boutique)"""
    try:
        with _get_connection() as conn:
            row = conn.execute(
                """
                SELECT p.id FROM products p
                JOIN shops s ON s.id = p.shop_id
                WHERE p.id = ? AND s.owner_user_id = ?
                """,
                (product_id, owner_user_id)
            ).fetchone()
            if not row:
                return False, "Produit introuvable"
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        return True, "Produit supprimé"
    except Exception as e:
        return False, str(e)


def update_order_status_if_shop(order_id: int, shop_id: int, status: str) -> bool:
    """Met à jour le statut d'une commande uniquement si elle appartient à la boutique"""
    try:
        with _get_connection() as conn:
            row = conn.execute(
                """
                SELECT o.id FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.id = ? AND p.shop_id = ?
                """,
                (order_id, shop_id)
            ).fetchone()
            if not row:
                return False
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        return True
    except Exception:
        return False


def list_shop_orders_anonymous(shop_id: int) -> List[sqlite3.Row]:
    """Liste les commandes d'une boutique SANS infos clients sensibles"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT o.id, o.quantity, o.total_amount, o.status, o.created_at,
                   p.name as product_name, p.image_url as product_image,
                   SUBSTR(u.full_name, 1, 1) || '***' || SUBSTR(u.full_name, -1) as client_name_masked
            FROM orders o
            JOIN products p ON o.product_id = p.id
            JOIN users u ON o.client_user_id = u.id
            WHERE p.shop_id = ?
            ORDER BY o.id DESC
            """,
            (shop_id,)
        ).fetchall()


def send_vendor_message(shop_id: int, subject: str, message: str) -> bool:
    """Envoie un message de la boutique à l'admin"""
    try:
        with _get_connection() as conn:
            row = conn.execute("SELECT owner_user_id FROM shops WHERE id = ?", (shop_id,)).fetchone()
            if not row:
                return False
            owner_id = row[0]
            conn.execute(
                """
                INSERT INTO vendor_admin_messages (shop_id, vendor_user_id, subject, message, created_at, is_from_vendor)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (shop_id, owner_id, subject, message, datetime.utcnow().isoformat())
            )
        return True
    except Exception:
        return False


def get_vendor_messages(shop_id: int) -> List[sqlite3.Row]:
    """Récupère les messages boutique <-> admin"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM vendor_admin_messages
            WHERE shop_id = ?
            ORDER BY created_at DESC
            """,
            (shop_id,)
        ).fetchall()


def mark_vendor_message_read(message_id: int) -> bool:
    """Marque un message comme lu"""
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE vendor_admin_messages SET is_read = 1 WHERE id = ?",
                (message_id,)
            )
        return True
    except Exception:
        return False


def get_all_vendor_admin_messages() -> List[sqlite3.Row]:
    """Récupère tous les messages boutique <-> admin"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT m.*, s.shop_name
            FROM vendor_admin_messages m
            JOIN shops s ON m.shop_id = s.id
            ORDER BY m.created_at DESC
            """
        ).fetchall()


def reply_vendor_message(message_id: int, reply: str) -> bool:
    """Répond à un message de boutique"""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                UPDATE vendor_admin_messages 
                SET admin_reply = ?, replied_at = ?, is_read = 0
                WHERE id = ?
                """,
                (reply, datetime.utcnow().isoformat(), message_id)
            )
        return True
    except Exception:
        return False


def send_message_to_shop(shop_id: int, subject: str, message: str) -> bool:
    """Envoie un message de l'admin à une boutique"""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO vendor_admin_messages (shop_id, vendor_user_id, subject, message, created_at, is_from_vendor, is_read)
                VALUES (?, NULL, ?, ?, ?, 0, 0)
                """,
                (shop_id, subject, message, datetime.utcnow().isoformat())
            )
        return True
    except Exception:
        return False


def get_all_shops_for_admin() -> List[sqlite3.Row]:
    """Récupère toutes les boutiques pour l'admin"""
    with _get_connection() as conn:
        return conn.execute("SELECT * FROM shops ORDER BY id DESC").fetchall()


# ============ JOURNAL D'ACTIVITÉ ============
def log_activity(user_id: int, user_name: str, action: str, details: str = "", ip_address: str = "") -> bool:
    """Enregistre une activité dans le journal"""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_log (user_id, user_name, action, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, user_name, action, details, ip_address, datetime.utcnow().isoformat())
            )
        return True
    except Exception:
        return False


def get_activity_log(limit: int = 100) -> List[sqlite3.Row]:
    """Récupère le journal d'activité"""
    with _get_connection() as conn:
        return conn.execute(
            "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()


# ============ TENTATIVES DE CONNEXION ============
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

def record_login_attempt(email: str, success: bool, ip_address: str = "") -> bool:
    """Enregistre une tentative de connexion"""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO login_attempts (email, ip_address, attempted_at, success)
                VALUES (?, ?, ?, ?)
                """,
                (email.lower(), ip_address, datetime.utcnow().isoformat(), 1 if success else 0)
            )
        return True
    except Exception:
        return False


def is_account_locked(email: str) -> tuple[bool, int]:
    """Vérifie si un compte est verrouillé"""
    cutoff_time = datetime.utcnow() - timedelta(minutes=LOCKOUT_MINUTES)
    with _get_connection() as conn:
        failed_attempts = conn.execute(
            """
            SELECT COUNT(*) FROM login_attempts
            WHERE email = ? AND success = 0 AND attempted_at > ?
            """,
            (email.lower(), cutoff_time.isoformat())
        ).fetchone()
        
        if failed_attempts:
            return failed_attempts[0] >= MAX_LOGIN_ATTEMPTS, failed_attempts[0]
        return False, 0


# ============ STATISTIQUES AVANCÉES ============
def get_daily_orders_stats(days: int = 30) -> List[sqlite3.Row]:
    """Statistiques des commandes par jour"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT DATE(created_at) as date, COUNT(*) as orders, SUM(total_amount) as revenue
            FROM orders
            WHERE created_at >= DATE('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,
            (f'-{days} days',)
        ).fetchall()


def get_popular_products(limit: int = 10) -> List[sqlite3.Row]:
    """Produits les plus commandés"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT p.id, p.name, p.image_url, COUNT(o.id) as order_count, SUM(o.total_amount) as total_sales
            FROM products p
            LEFT JOIN orders o ON p.id = o.product_id
            GROUP BY p.id
            ORDER BY order_count DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()


def get_monthly_stats() -> List[sqlite3.Row]:
    """Statistiques mensuelles"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT strftime('%Y-%m', created_at) as month,
                   COUNT(*) as orders,
                   SUM(total_amount) as revenue
            FROM orders
            WHERE created_at >= DATE('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month DESC
            """
        ).fetchall()


def get_shop_monthly_stats(shop_id: int) -> List[sqlite3.Row]:
    """Statistiques mensuelles d'une boutique"""
    with _get_connection() as conn:
        return conn.execute(
            """
            SELECT strftime('%Y-%m', o.created_at) as month,
                   COUNT(*) as orders,
                   SUM(o.total_amount) as revenue
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE p.shop_id = ? AND o.created_at >= DATE('now', '-12 months')
            GROUP BY strftime('%Y-%m', o.created_at)
            ORDER BY month DESC
            """,
            (shop_id,)
        ).fetchall()


# ============ CONVERSATIONS CLIENT ============
def get_client_conversations() -> List[Dict[str, Any]]:
    """Récupère les conversations clients groupées par utilisateur"""
    with _get_connection() as conn:
        conversations = conn.execute("""
            SELECT 
                m.user_id,
                u.full_name,
                u.email,
                COUNT(m.id) as message_count,
                MAX(m.created_at) as last_message_at,
                SUM(CASE WHEN m.is_read = 0 AND m.is_from_admin = 1 THEN 1 ELSE 0 END) as unread_admin,
                SUM(CASE WHEN m.is_read = 0 AND m.is_from_admin = 0 THEN 1 ELSE 0 END) as unread_client
            FROM admin_messages m
            JOIN users u ON m.user_id = u.id
            GROUP BY m.user_id
            ORDER BY last_message_at DESC
        """).fetchall()
        return [dict(row) for row in conversations]


def get_client_conversation(user_id: int) -> List[sqlite3.Row]:
    """Récupère tous les messages d'une conversation client"""
    with _get_connection() as conn:
        return conn.execute("""
            SELECT * FROM admin_messages 
            WHERE user_id = ?
            ORDER BY created_at ASC
        """, (user_id,)).fetchall()


def mark_client_conversation_read(user_id: int) -> bool:
    """Marque tous les messages d'un client comme lus"""
    try:
        with _get_connection() as conn:
            conn.execute("UPDATE admin_messages SET is_read = 1 WHERE user_id = ?", (user_id,))
        return True
    except Exception:
        return False


def count_unread_client_conversations() -> int:
    """Compte les conversations avec des messages non lus du client"""
    with _get_connection() as conn:
        result = conn.execute("""
            SELECT COUNT(DISTINCT user_id) 
            FROM admin_messages 
            WHERE is_read = 0 AND is_from_admin = 0
        """).fetchone()
        return result[0] if result else 0


# ============ CONVERSATIONS BOUTIQUE ============
def get_shop_conversations() -> List[Dict[str, Any]]:
    """Récupère les conversations boutiques groupées"""
    with _get_connection() as conn:
        conversations = conn.execute("""
            SELECT 
                m.shop_id,
                s.shop_name,
                COUNT(m.id) as message_count,
                MAX(m.created_at) as last_message_at,
                SUM(CASE WHEN m.is_read = 0 AND m.is_from_vendor = 1 THEN 1 ELSE 0 END) as unread_vendor,
                SUM(CASE WHEN m.is_read = 0 AND m.is_from_vendor = 0 THEN 1 ELSE 0 END) as unread_admin
            FROM vendor_admin_messages m
            JOIN shops s ON m.shop_id = s.id
            GROUP BY m.shop_id
            ORDER BY last_message_at DESC
        """).fetchall()
        return [dict(row) for row in conversations]


def get_shop_conversation(shop_id: int) -> List[sqlite3.Row]:
    """Récupère tous les messages d'une conversation boutique"""
    with _get_connection() as conn:
        return conn.execute("""
            SELECT * FROM vendor_admin_messages 
            WHERE shop_id = ?
            ORDER BY created_at ASC
        """, (shop_id,)).fetchall()


def mark_shop_conversation_read(shop_id: int) -> bool:
    """Marque tous les messages d'une boutique comme lus par l'admin"""
    try:
        with _get_connection() as conn:
            conn.execute("UPDATE vendor_admin_messages SET is_read = 1 WHERE shop_id = ? AND is_from_vendor = 1", (shop_id,))
        return True
    except Exception:
        return False


def count_unread_shop_conversations() -> int:
    """Compte les conversations boutiques avec des messages non lus"""
    with _get_connection() as conn:
        result = conn.execute("""
            SELECT COUNT(DISTINCT shop_id) 
            FROM vendor_admin_messages 
            WHERE is_read = 0 AND is_from_vendor = 1
        """).fetchone()
        return result[0] if result else 0


# ============ GESTION BOUTIQUES ============
def get_shop_with_owner(shop_id: int) -> Optional[Dict[str, Any]]:
    """Récupère une boutique avec les infos du propriétaire"""
    with _get_connection() as conn:
        row = conn.execute("""
            SELECT s.*, u.id as owner_user_id, u.full_name as owner_name, u.email as owner_email
            FROM shops s
            JOIN users u ON s.owner_user_id = u.id
            WHERE s.id = ?
        """, (shop_id,)).fetchone()
        if row:
            return dict(row)
        return None


def update_shop_credentials(shop_id: int, owner_name: str = None, password: str = None) -> Tuple[bool, str]:
    """Modifie les identifiants d'une boutique (nom et/ou mot de passe)"""
    try:
        with _get_connection() as conn:
            shop = conn.execute("SELECT owner_user_id FROM shops WHERE id = ?", (shop_id,)).fetchone()
            if not shop:
                return False, "Boutique introuvable"
            
            owner_id = shop[0]
            
            if owner_name:
                conn.execute("UPDATE users SET full_name = ? WHERE id = ?", (owner_name.strip(), owner_id))
            
            if password:
                if len(password) < 8:
                    return False, "Le mot de passe doit contenir au moins 8 caractères"
                salt, pwd_hash = _hash_password(password)
                conn.execute(
                    "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
                    (pwd_hash, salt, owner_id)
                )
            
            return True, "Identifiants mis à jour"
    except Exception as e:
        return False, str(e)


def update_shop_info(shop_id: int, shop_name: str = None, description: str = None, contact_info: str = None) -> Tuple[bool, str]:
    """Modifie les informations d'une boutique"""
    try:
        with _get_connection() as conn:
            updates = []
            params = []
            
            if shop_name:
                updates.append("shop_name = ?")
                params.append(shop_name.strip())
            if description is not None:
                updates.append("description = ?")
                params.append(description.strip())
            if contact_info is not None:
                updates.append("contact_info = ?")
                params.append(contact_info.strip())
            
            if not updates:
                return False, "Aucune modification"
            
            params.append(shop_id)
            conn.execute(f"UPDATE shops SET {', '.join(updates)} WHERE id = ?", params)
            return True, "Boutique mise à jour"
    except sqlite3.IntegrityError:
        return False, "Nom de boutique déjà utilisé"
    except Exception as e:
        return False, str(e)
