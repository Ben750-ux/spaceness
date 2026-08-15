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


def _ensure_column_exists(conn: sqlite3.Connection, table_name: str, column_name: str, column_def: str) -> None:
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    names = {c["name"] for c in cols}
    if column_name not in names:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(c["name"] == column for c in cols)


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute("""
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
        """)
        verify_col_exists = _column_exists(conn, "users", "is_verified")
        _ensure_column_exists(conn, "users", "is_verified", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column_exists(conn, "users", "verification_code", "TEXT")
        _ensure_column_exists(conn, "users", "verification_code_expires", "TEXT")
        if not verify_col_exists:
            conn.execute("UPDATE users SET is_verified = 1")

        conn.execute("""
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
        """)
        _ensure_column_exists(conn, "shops", "logo_url", "TEXT NOT NULL DEFAULT ''")
        _ensure_column_exists(conn, "shops", "banner_url", "TEXT NOT NULL DEFAULT ''")

        conn.execute("""
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
        """)
        _ensure_column_exists(conn, "products", "image_url", "TEXT NOT NULL DEFAULT ''")
        _ensure_column_exists(conn, "products", "image_url_2", "TEXT NOT NULL DEFAULT ''")
        _ensure_column_exists(conn, "products", "image_url_3", "TEXT NOT NULL DEFAULT ''")

        conn.execute("""
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
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_shop_id ON products(shop_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_user_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS shop_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_user_id INTEGER NOT NULL,
                shop_id INTEGER NOT NULL,
                subscribed_at TEXT NOT NULL,
                FOREIGN KEY(client_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(shop_id) REFERENCES shops(id) ON DELETE CASCADE,
                UNIQUE(client_user_id, shop_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_client ON shop_subscriptions(client_user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_shop ON shop_subscriptions(shop_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE(user_id, product_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS view_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                viewed_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON view_history(user_id)")

        conn.execute("""
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
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product ON product_reviews(product_id)")

        conn.execute("""
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
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON admin_messages(user_id)")
        _ensure_column_exists(conn, "admin_messages", "is_from_admin", "INTEGER NOT NULL DEFAULT 0")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                block_message TEXT NOT NULL DEFAULT ''
            )
        """)
        existing = conn.execute("SELECT id FROM app_settings WHERE id = 1").fetchone()
        if not existing:
            conn.execute("INSERT INTO app_settings (id, is_blocked, block_message) VALUES (1, 0, '')")

        conn.execute("""
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
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vendor_messages_shop ON vendor_admin_messages(shop_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                attempted_at TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log(user_id)")


# ============ AUTH ============
def create_user(full_name: str, email: str, password: str, role: str) -> Tuple[bool, str]:
    if role not in {"client", "boutique"}:
        return False, "Role invalide."
    if len(password) < 6:
        return False, "Le mot de passe doit avoir au moins 6 caracteres."
    try:
        with _get_connection() as conn:
            salt, pwd_hash = _hash_password(password)
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash, password_salt, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (full_name.strip(), email.strip().lower(), pwd_hash, salt, role, datetime.utcnow().isoformat()),
            )
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            if role == "boutique":
                shop_name = f"{full_name.strip()} Shop"
                conn.execute(
                    "INSERT INTO shops (owner_user_id, shop_name, description, contact_info) VALUES (?, ?, '', '')",
                    (user_id, shop_name),
                )
        return True, "Compte cree avec succes."
    except sqlite3.IntegrityError:
        return False, "Cet email est deja utilise."


def login_user(email: str, password: str) -> Tuple[bool, str, Any]:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT id, full_name, email, password_hash, password_salt, role, is_blocked, is_verified FROM users WHERE email = ?",
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
        return True, "Connexion reussie.", {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
        }


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT id, full_name, email, role, is_blocked, is_verified FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row or row["is_blocked"]:
            return None
        return dict(row)


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


# ============ BOUTIQUES ============
def get_shop_by_owner(owner_user_id: int):
    with _get_connection() as conn:
        row = conn.execute("SELECT * FROM shops WHERE owner_user_id = ?", (owner_user_id,)).fetchone()
        return dict(row) if row else None


def get_shop_details(shop_id: int):
    with _get_connection() as conn:
        row = conn.execute("SELECT * FROM shops WHERE id = ?", (shop_id,)).fetchone()
        return dict(row) if row else None


def update_shop(owner_user_id: int, shop_name: str, description: str, contact_info: str, logo_url: str, banner_url: str) -> Tuple[bool, str]:
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE shops SET shop_name = ?, description = ?, contact_info = ?, logo_url = ?, banner_url = ? WHERE owner_user_id = ?",
                (shop_name.strip(), description.strip(), contact_info.strip(), logo_url.strip(), banner_url.strip(), owner_user_id),
            )
        return True, "Profil boutique mis a jour."
    except sqlite3.IntegrityError:
        return False, "Nom de boutique deja utilise."


# ============ PRODUITS ============
def add_product(owner_user_id: int, name: str, category: str, price: float, stock: int, description: str, image_url: str) -> Tuple[bool, str]:
    shop = get_shop_by_owner(owner_user_id)
    if not shop:
        return False, "Boutique introuvable."
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO products (shop_id, name, category, price, stock, description, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (shop["id"], name.strip(), category.strip() or "General", price, stock, description.strip(), image_url.strip()),
        )
    return True, "Produit ajoute."


def update_product_stock(product_id: int, owner_user_id: int, stock: int, is_active: int) -> Tuple[bool, str]:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT p.id FROM products p JOIN shops s ON s.id = p.shop_id WHERE p.id = ? AND s.owner_user_id = ?",
            (product_id, owner_user_id),
        ).fetchone()
        if not row:
            return False, "Produit introuvable."
        conn.execute("UPDATE products SET stock = ?, is_active = ? WHERE id = ?", (stock, is_active, product_id))
    return True, "Produit mis a jour."


def list_shop_products(shop_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, category, price, stock, description, image_url, image_url_2, image_url_3, is_active FROM products WHERE shop_id = ? ORDER BY id DESC",
            (shop_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_market_products(search: str = "", category: str = "") -> List[Dict[str, Any]]:
    search = search.strip().lower()
    category = category.strip().lower()
    base = """
        SELECT p.id, p.name, p.category, p.price, p.stock, p.description,
               p.image_url, p.image_url_2, p.image_url_3,
               s.id AS shop_id, s.shop_name
        FROM products p JOIN shops s ON s.id = p.shop_id
        WHERE p.is_active = 1 AND p.stock > 0
    """
    params = []
    if search:
        base += " AND (LOWER(p.name) LIKE ? OR LOWER(s.shop_name) LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    if category:
        base += " AND LOWER(p.category) = ?"
        params.append(category)
    base += " ORDER BY p.id DESC"
    with _get_connection() as conn:
        rows = conn.execute(base, tuple(params)).fetchall()
        return [dict(r) for r in rows]


def get_product_by_id(product_id: int):
    with _get_connection() as conn:
        row = conn.execute(
            """SELECT p.id, p.name, p.category, p.price, p.stock, p.description,
                      p.image_url, p.image_url_2, p.image_url_3, p.is_active,
                      s.id AS shop_id, s.shop_name
               FROM products p JOIN shops s ON s.id = p.shop_id WHERE p.id = ?""",
            (product_id,),
        ).fetchone()
        return dict(row) if row else None


# ============ COMMANDES ============
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
            "INSERT INTO orders (client_user_id, product_id, quantity, total_amount, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
            (client_user_id, product_id, quantity, total, datetime.utcnow().isoformat()),
        )
        conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    return True, "Commande enregistree."


def list_orders_for_client(client_user_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT o.id, o.quantity, o.total_amount, o.status, o.created_at,
                      p.id AS product_id, p.name AS product_name, p.description AS product_description,
                      p.price AS product_price, p.image_url AS product_image_url,
                      p.image_url_2 AS product_image_url_2, p.image_url_3 AS product_image_url_3,
                      p.category AS product_category, s.id AS shop_id, s.shop_name, s.logo_url AS shop_logo_url
               FROM orders o JOIN products p ON p.id = o.product_id JOIN shops s ON s.id = p.shop_id
               WHERE o.client_user_id = ? ORDER BY o.id DESC""",
            (client_user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ============ FAVORIS ============
def add_to_favorites(user_id: int, product_id: int) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO favorites (user_id, product_id, created_at) VALUES (?, ?, ?)",
                (user_id, product_id, datetime.utcnow().isoformat()),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def remove_from_favorites(user_id: int, product_id: int) -> bool:
    with _get_connection() as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        conn.commit()
    return True


def is_favorite(user_id: int, product_id: int) -> bool:
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT id FROM favorites WHERE user_id = ? AND product_id = ?", (user_id, product_id)
        ).fetchone()
        return result is not None


def list_favorites(user_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT p.id, p.name, p.category, p.price, p.stock, p.description,
                      p.image_url, p.image_url_2, p.image_url_3,
                      s.id AS shop_id, s.shop_name, f.created_at AS favorited_at
               FROM favorites f JOIN products p ON p.id = f.product_id
               JOIN shops s ON s.id = p.shop_id WHERE f.user_id = ? ORDER BY f.created_at DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ============ HISTORIQUE ============
def add_to_history(user_id: int, product_id: int) -> None:
    with _get_connection() as conn:
        conn.execute("DELETE FROM view_history WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        conn.execute(
            "INSERT INTO view_history (user_id, product_id, viewed_at) VALUES (?, ?, ?)",
            (user_id, product_id, datetime.utcnow().isoformat()),
        )
        conn.execute(
            "DELETE FROM view_history WHERE user_id = ? AND id NOT IN (SELECT id FROM view_history WHERE user_id = ? ORDER BY viewed_at DESC LIMIT 50)",
            (user_id, user_id),
        )
        conn.commit()


def list_history(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT p.id, p.name, p.category, p.price, p.stock, p.description,
                      p.image_url, p.image_url_2, p.image_url_3,
                      s.id AS shop_id, s.shop_name, h.viewed_at
               FROM view_history h JOIN products p ON p.id = h.product_id
               JOIN shops s ON s.id = p.shop_id
               WHERE h.user_id = ? ORDER BY h.viewed_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def clear_history(user_id: int) -> None:
    with _get_connection() as conn:
        conn.execute("DELETE FROM view_history WHERE user_id = ?", (user_id,))
        conn.commit()


# ============ AVIS ============
def add_review(user_id: int, product_id: int, rating: int, comment: str = "") -> bool:
    if not 1 <= rating <= 5:
        return False
    with _get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO product_reviews (user_id, product_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, product_id, rating, comment, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE product_reviews SET rating = ?, comment = ?, created_at = ? WHERE user_id = ? AND product_id = ?",
                (rating, comment, datetime.utcnow().isoformat(), user_id, product_id),
            )
            conn.commit()
            return True


def get_product_reviews(product_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT r.*, u.full_name AS user_name FROM product_reviews r JOIN users u ON u.id = r.user_id WHERE r.product_id = ? ORDER BY r.created_at DESC",
            (product_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_product_rating(product_id: int) -> Tuple[float, int]:
    with _get_connection() as conn:
        result = conn.execute(
            "SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM product_reviews WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        avg = result["avg_rating"] if result["avg_rating"] else 0.0
        count = result["count"] or 0
        return (round(avg, 1), count)


def get_user_review(user_id: int, product_id: int):
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM product_reviews WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        return dict(row) if row else None


# ============ ABONNEMENTS ============
def is_subscribed_to_shop(client_user_id: int, shop_id: int) -> bool:
    with _get_connection() as conn:
        return conn.execute(
            "SELECT id FROM shop_subscriptions WHERE client_user_id = ? AND shop_id = ?",
            (client_user_id, shop_id),
        ).fetchone() is not None


def subscribe_to_shop(client_user_id: int, shop_id: int) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO shop_subscriptions (client_user_id, shop_id, subscribed_at) VALUES (?, ?, ?)",
                (client_user_id, shop_id, datetime.utcnow().isoformat()),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def unsubscribe_from_shop(client_user_id: int, shop_id: int) -> bool:
    with _get_connection() as conn:
        conn.execute(
            "DELETE FROM shop_subscriptions WHERE client_user_id = ? AND shop_id = ?",
            (client_user_id, shop_id),
        )
        conn.commit()
    return True


def get_shop_subscriber_count(shop_id: int) -> int:
    with _get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM shop_subscriptions WHERE shop_id = ?", (shop_id,)).fetchone()
        return result[0] if result else 0


def list_subscribed_shops(client_user_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT s.id, s.shop_name, s.logo_url, s.description, sub.subscribed_at
               FROM shops s JOIN shop_subscriptions sub ON s.id = sub.shop_id
               WHERE sub.client_user_id = ? ORDER BY sub.subscribed_at DESC""",
            (client_user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_subscribed_shop_products(client_user_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT p.*, s.shop_name, s.logo_url AS shop_logo_url, 1 AS is_subscribed
               FROM products p JOIN shops s ON p.shop_id = s.id
               JOIN shop_subscriptions sub ON s.id = sub.shop_id
               WHERE sub.client_user_id = ? AND p.is_active = 1 ORDER BY p.id DESC""",
            (client_user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ============ UTILISATEURS (ADMIN) ============
def list_all_users() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT id, full_name, email, role, is_blocked, created_at FROM users ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


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


def toggle_user_block(user_id: int, blocked: bool) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute("UPDATE users SET is_blocked = ? WHERE id = ?", (1 if blocked else 0, user_id))
        return True
    except Exception:
        return False


# ============ ADMIN MESSAGES ============
def send_admin_message(user_id: int, subject: str, message: str, is_from_admin: bool = False) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO admin_messages (user_id, subject, message, created_at, is_from_admin) VALUES (?, ?, ?, ?, ?)",
                (user_id, subject, message, datetime.utcnow().isoformat(), 1 if is_from_admin else 0),
            )
        return True
    except Exception:
        return False


def get_user_messages(user_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM admin_messages WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_messages() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT m.*, u.full_name, u.email FROM admin_messages m JOIN users u ON m.user_id = u.id ORDER BY m.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def reply_to_message(message_id: int, reply: str) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE admin_messages SET admin_reply = ?, replied_at = ?, is_read = 0 WHERE id = ?",
                (reply, datetime.utcnow().isoformat(), message_id),
            )
        return True
    except Exception:
        return False


def mark_message_read(message_id: int) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute("UPDATE admin_messages SET is_read = 1 WHERE id = ?", (message_id,))
        return True
    except Exception:
        return False


def count_unread_messages() -> int:
    with _get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM admin_messages WHERE is_read = 0").fetchone()
        return result[0] if result else 0


# ============ COMMANDES (ADMIN) ============
def update_order_status(order_id: int, status: str) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        return True
    except Exception:
        return False


def list_all_orders() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT o.*, p.name as product_name, u.full_name as client_name, s.shop_name
               FROM orders o JOIN products p ON o.product_id = p.id
               JOIN users u ON o.client_user_id = u.id
               JOIN shops s ON p.shop_id = s.id ORDER BY o.id DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


# ============ STATS ============
def count_users() -> int:
    with _get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def count_products() -> int:
    with _get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]


def count_orders() -> int:
    with _get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]


def count_shops() -> int:
    with _get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM shops").fetchone()[0]


def list_all_products() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT p.*, s.shop_name FROM products p JOIN shops s ON p.shop_id = s.id ORDER BY p.id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def list_all_shops() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute("SELECT * FROM shops ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_app_settings() -> Dict[str, Any]:
    with _get_connection() as conn:
        row = conn.execute("SELECT is_blocked, block_message FROM app_settings WHERE id = 1").fetchone()
        if row:
            return {"is_blocked": bool(row[0]), "block_message": row[1]}
        return {"is_blocked": False, "block_message": ""}


def set_app_blocked(is_blocked: bool, block_message: str) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE app_settings SET is_blocked = ?, block_message = ? WHERE id = 1",
                (1 if is_blocked else 0, block_message),
            )
        return True
    except Exception:
        return False


# ============ TENTATIVES DE CONNEXION ============
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def record_login_attempt(email: str, success: bool, ip_address: str = "") -> bool:
    try:
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO login_attempts (email, ip_address, attempted_at, success) VALUES (?, ?, ?, ?)",
                (email.lower(), ip_address, datetime.utcnow().isoformat(), 1 if success else 0),
            )
        return True
    except Exception:
        return False


def is_account_locked(email: str) -> Tuple[bool, int]:
    cutoff = datetime.utcnow() - timedelta(minutes=LOCKOUT_MINUTES)
    with _get_connection() as conn:
        failed = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE email = ? AND success = 0 AND attempted_at > ?",
            (email.lower(), cutoff.isoformat()),
        ).fetchone()
        count = failed[0] if failed else 0
        return count >= MAX_LOGIN_ATTEMPTS, count


# ============ MESSAGES BOUTIQUE ============
def send_vendor_message(shop_id: int, subject: str, message: str) -> bool:
    try:
        with _get_connection() as conn:
            row = conn.execute("SELECT owner_user_id FROM shops WHERE id = ?", (shop_id,)).fetchone()
            if not row:
                return False
            conn.execute(
                "INSERT INTO vendor_admin_messages (shop_id, vendor_user_id, subject, message, created_at, is_from_vendor) VALUES (?, ?, ?, ?, ?, 1)",
                (shop_id, row[0], subject, message, datetime.utcnow().isoformat()),
            )
        return True
    except Exception:
        return False


def get_vendor_messages(shop_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM vendor_admin_messages WHERE shop_id = ? ORDER BY created_at DESC", (shop_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def reply_vendor_message(message_id: int, reply: str) -> bool:
    try:
        with _get_connection() as conn:
            conn.execute(
                "UPDATE vendor_admin_messages SET admin_reply = ?, replied_at = ?, is_read = 0 WHERE id = ?",
                (reply, datetime.utcnow().isoformat(), message_id),
            )
        return True
    except Exception:
        return False
