import json
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.parse import urlencode

API_URL = os.environ.get("API_URL", "https://spaceness.onrender.com")


def _api_url(path: str) -> str:
    return f"{API_URL}{path}"


def _request(method: str, url: str, data: Any = None) -> Any:
    from urllib.error import HTTPError
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        detail = str(e)
        try:
            body = e.read().decode()
            detail = json.loads(body).get("detail", detail)
        except Exception:
            pass
        return {"ok": False, "detail": detail}
    except Exception as e:
        return {"ok": False, "detail": str(e)}


def _get(path: str) -> Any:
    return _request("GET", _api_url(path))


def _post(path: str, data: Any) -> Any:
    return _request("POST", _api_url(path), data)


# ============ UTILITAIRES ============
def init_db() -> None:
    pass


# ============ AUTH ============
def create_user(full_name: str, email: str, password: str, role: str) -> Tuple[bool, str]:
    resp = _post("/api/auth/register", {"full_name": full_name, "email": email, "password": password, "role": role})
    if resp.get("ok"):
        return True, resp.get("message", "Compte cree.")
    return False, resp.get("detail", "Erreur lors de la creation du compte.")


def forgot_password(email: str) -> Tuple[bool, str]:
    resp = _post("/api/auth/forgot-password", {"email": email})
    if resp.get("ok"):
        return True, resp.get("code", "")
    return False, resp.get("detail", "Erreur lors de l'envoi du code.")

def reset_password(email: str, code: str, new_password: str) -> Tuple[bool, str]:
    resp = _post("/api/auth/reset-password", {"email": email, "code": code, "new_password": new_password})
    if resp.get("ok"):
        return True, resp.get("message", "Mot de passe reinitialise.")
    return False, resp.get("detail", "Erreur lors de la reinitialisation.")

def login_user(email: str, password: str) -> Tuple[bool, str, Any]:
    resp = _post("/api/auth/login", {"email": email, "password": password})
    if resp.get("verification_required"):
        return False, "VERIFICATION_REQUIRED", resp.get("user")
    if resp.get("ok"):
        return True, resp.get("message", "Connexion reussie."), resp.get("user")
    return False, resp.get("detail", "Email ou mot de passe incorrect."), None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    resp = _post("/api/auth/get-user", {"user_id": user_id})
    return resp.get("user") if resp.get("ok") else None


def generate_verification_code() -> str:
    import random
    return str(random.randint(100000, 999999))


def save_verification_code(user_id: int, code: str) -> None:
    _post("/api/auth/save-code", {"user_id": user_id, "code": code})


def resend_verification_code(user_id: int) -> Optional[str]:
    resp = _post("/api/auth/resend-code", {"user_id": user_id})
    return resp.get("code") if resp.get("ok") else None


def verify_email_code(user_id: int, code: str) -> Tuple[bool, str]:
    resp = _post("/api/auth/verify-code", {"user_id": user_id, "code": code})
    if resp.get("ok"):
        return True, resp.get("message", "Email verifie !")
    return False, resp.get("detail", "Code incorrect.")


def is_user_verified(user_id: int) -> bool:
    user = get_user_by_id(user_id)
    return bool(user and user.get("is_verified"))


# ============ BOUTIQUES ============
def get_shop_by_owner(owner_user_id: int) -> Optional[Dict[str, Any]]:
    shops = _get("/api/admin/shops").get("shops", [])
    for s in shops:
        if s.get("owner_user_id") == owner_user_id:
            return s
    return None


def get_shop_details(shop_id: int) -> Optional[Dict[str, Any]]:
    resp = _get(f"/api/shops/{shop_id}")
    return resp.get("shop") if resp.get("ok") else None


def update_shop(owner_user_id: int, shop_name: str, description: str = "", contact_info: str = "", logo_url: str = "", banner_url: str = "") -> Tuple[bool, str]:
    resp = _post("/api/shops/update", {
        "owner_user_id": owner_user_id, "shop_name": shop_name,
        "description": description, "contact_info": contact_info,
        "logo_url": logo_url, "banner_url": banner_url,
    })
    if resp.get("ok"):
        return True, resp.get("message", "Boutique mise a jour.")
    return False, resp.get("detail", "Erreur.")


# ============ PRODUITS ============
def add_product(owner_user_id: int, name: str, category: str, price: float, stock: int, description: str = "", image_url: str = "") -> Tuple[bool, str]:
    resp = _post("/api/products/add", {
        "owner_user_id": owner_user_id, "name": name, "category": category,
        "price": price, "stock": stock, "description": description, "image_url": image_url,
    })
    if resp.get("ok"):
        return True, resp.get("message", "Produit ajoute.")
    return False, resp.get("detail", "Erreur.")


def update_product_stock(product_id: int, owner_user_id: int, stock: int, is_active: int) -> Tuple[bool, str]:
    resp = _post("/api/products/update-stock", {
        "product_id": product_id, "owner_user_id": owner_user_id,
        "stock": stock, "is_active": is_active,
    })
    if resp.get("ok"):
        return True, resp.get("message", "Produit mis a jour.")
    return False, resp.get("detail", "Erreur.")


def list_shop_products(shop_id: int) -> List[Dict[str, Any]]:
    resp = _get(f"/api/shops/{shop_id}/products")
    return resp.get("products", [])


def list_market_products(search: str = "", category: str = "") -> List[Dict[str, Any]]:
    params = {}
    if search:
        params["search"] = search
    if category:
        params["category"] = category
    url = f"/api/products"
    if params:
        url += f"?{urlencode(params)}"
    resp = _get(url)
    return resp.get("products", [])


def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    resp = _get(f"/api/products/{product_id}")
    return resp.get("product") if resp.get("ok") else None


# ============ COMMANDES ============
def place_order(client_user_id: int, product_id: int, quantity: int) -> Tuple[bool, str]:
    resp = _post("/api/orders/place", {
        "client_user_id": client_user_id, "product_id": product_id, "quantity": quantity,
    })
    if resp.get("ok"):
        return True, resp.get("message", "Commande enregistree.")
    return False, resp.get("detail", "Erreur.")


def list_orders_for_client(client_user_id: int) -> List[Dict[str, Any]]:
    resp = _get(f"/api/orders/client/{client_user_id}")
    return resp.get("orders", [])


# ============ FAVORIS ============
def add_to_favorites(user_id: int, product_id: int) -> bool:
    resp = _post("/api/favorites/add", {"user_id": user_id, "product_id": product_id})
    return resp.get("ok", False)


def remove_from_favorites(user_id: int, product_id: int) -> bool:
    resp = _post("/api/favorites/remove", {"user_id": user_id, "product_id": product_id})
    return resp.get("ok", False)


def is_favorite(user_id: int, product_id: int) -> bool:
    resp = _post("/api/favorites/check", {"user_id": user_id, "product_id": product_id})
    return resp.get("is_favorite", False)


def list_favorites(user_id: int) -> List[Dict[str, Any]]:
    resp = _get(f"/api/favorites/{user_id}")
    return resp.get("favorites", [])


# ============ HISTORIQUE ============
def add_to_history(user_id: int, product_id: int) -> None:
    _post("/api/history/add", {"user_id": user_id, "product_id": product_id})


def list_history(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    resp = _get(f"/api/history/{user_id}")
    return resp.get("history", [])


def clear_history(user_id: int) -> None:
    _post("/api/history/clear", {"user_id": user_id})


# ============ AVIS ============
def add_review(user_id: int, product_id: int, rating: int, comment: str = "") -> bool:
    resp = _post("/api/reviews/add", {
        "user_id": user_id, "product_id": product_id, "rating": rating, "comment": comment,
    })
    return resp.get("ok", False)


def get_product_reviews(product_id: int) -> List[Dict[str, Any]]:
    resp = _get(f"/api/reviews/{product_id}")
    return resp.get("reviews", [])


def get_product_rating(product_id: int) -> Tuple[float, int]:
    resp = _get(f"/api/reviews/{product_id}")
    return (resp.get("rating", 0.0), resp.get("count", 0))


def get_user_review(user_id: int, product_id: int) -> Optional[Dict[str, Any]]:
    reviews = _get(f"/api/reviews/{product_id}").get("reviews", [])
    for r in reviews:
        if r.get("user_id") == user_id:
            return r
    return None


# ============ ABONNEMENTS ============
def is_subscribed_to_shop(client_user_id: int, shop_id: int) -> bool:
    shops = _get(f"/api/subscriptions/{client_user_id}").get("shops", [])
    return any(s.get("id") == shop_id for s in shops)


def subscribe_to_shop(client_user_id: int, shop_id: int) -> bool:
    resp = _post("/api/subscriptions/subscribe", {
        "client_user_id": client_user_id, "shop_id": shop_id,
    })
    return resp.get("ok", False)


def unsubscribe_from_shop(client_user_id: int, shop_id: int) -> bool:
    resp = _post("/api/subscriptions/unsubscribe", {
        "client_user_id": client_user_id, "shop_id": shop_id,
    })
    return resp.get("ok", False)


def get_shop_subscriber_count(shop_id: int) -> int:
    shop = get_shop_details(shop_id)
    return 0


def list_subscribed_shops(client_user_id: int) -> List[Dict[str, Any]]:
    resp = _get(f"/api/subscriptions/{client_user_id}")
    return resp.get("shops", [])


def get_subscribed_shop_products(client_user_id: int) -> List[Dict[str, Any]]:
    resp = _get(f"/api/subscriptions/{client_user_id}/products")
    return resp.get("products", [])


# ============ ADMIN ============
def list_all_users() -> List[Dict[str, Any]]:
    resp = _get("/api/admin/users")
    return resp.get("users", [])


def set_user_block_status(user_id: int, blocked: int) -> Tuple[bool, str]:
    resp = _post("/api/admin/users/block", {"user_id": user_id, "blocked": blocked})
    if resp.get("ok"):
        return True, resp.get("message", "Statut mis a jour.")
    return False, resp.get("detail", "Erreur.")


def delete_user(user_id: int) -> Tuple[bool, str]:
    resp = _post("/api/admin/users/delete", {"user_id": user_id})
    if resp.get("ok"):
        return True, resp.get("message", "Utilisateur supprime.")
    return False, resp.get("detail", "Erreur.")


def toggle_user_block(user_id: int, blocked: bool) -> bool:
    _, _ = set_user_block_status(user_id, 1 if blocked else 0)
    return True


def update_order_status(order_id: int, status: str) -> bool:
    resp = _post("/api/orders/update-status", {"order_id": order_id, "status": status})
    return resp.get("ok", False)


def list_all_orders() -> List[Dict[str, Any]]:
    resp = _get("/api/admin/orders")
    return resp.get("orders", [])


def list_all_products() -> List[Dict[str, Any]]:
    resp = _get("/api/admin/products")
    return resp.get("products", [])


def list_all_shops() -> List[Dict[str, Any]]:
    resp = _get("/api/admin/shops")
    return resp.get("shops", [])


def count_users() -> int:
    return _get("/api/admin/stats").get("users", 0)


def count_products() -> int:
    return _get("/api/admin/stats").get("products", 0)


def count_orders() -> int:
    return _get("/api/admin/stats").get("orders", 0)


def count_shops() -> int:
    return _get("/api/admin/stats").get("shops", 0)


# ============ MESSAGES ============
def send_admin_message(user_id: int, subject: str, message: str, is_from_admin: bool = False) -> bool:
    resp = _post("/api/messages/send", {
        "user_id": user_id, "subject": subject, "message": message,
    })
    return resp.get("ok", False)


def get_user_messages(user_id: int) -> List[Dict[str, Any]]:
    resp = _get(f"/api/messages/{user_id}")
    return resp.get("messages", [])


def get_all_messages() -> List[Dict[str, Any]]:
    resp = _get("/api/admin/messages")
    return resp.get("messages", [])


def reply_to_message(message_id: int, reply: str) -> bool:
    resp = _post("/api/admin/messages/reply", {"message_id": message_id, "reply": reply})
    return resp.get("ok", False)


def mark_message_read(message_id: int) -> bool:
    resp = _post("/api/admin/messages/read", {"message_id": message_id})
    return resp.get("ok", False)


def count_unread_messages() -> int:
    return _get("/api/admin/messages/unread-count").get("count", 0)


# ============ PARAMÈTRES APP ============
def get_app_settings() -> Dict[str, Any]:
    resp = _get("/api/app-settings")
    return resp.get("settings", {"is_blocked": False, "block_message": ""})


def set_app_blocked(is_blocked: bool, block_message: str = "") -> bool:
    resp = _post(f"/api/app-settings?is_blocked={str(is_blocked).lower()}&block_message={block_message}", None)
    return resp.get("ok", False)


# ============ NON IMPLÉMENTÉ (local only) ============
def create_vendor_account(full_name: str, email: str, password: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    return False, "Non disponible en ligne.", None


def get_shop_with_owner(shop_id: int) -> Optional[Dict[str, Any]]:
    shop = get_shop_details(shop_id)
    return shop


def update_shop_credentials(shop_id: int, owner_name: str = None, password: str = None) -> Tuple[bool, str]:
    return False, "Non disponible en ligne."


def update_shop_info(shop_id: int, shop_name: str = None, description: str = None, contact_info: str = None) -> Tuple[bool, str]:
    return False, "Non disponible en ligne."


def get_vendor_messages(shop_id: int) -> List[Dict[str, Any]]:
    return []


def send_vendor_message(shop_id: int, subject: str, message: str) -> bool:
    return False


def reply_vendor_message(message_id: int, reply: str) -> bool:
    return False


def get_all_vendor_admin_messages() -> List[Dict[str, Any]]:
    return []


def send_message_to_shop(shop_id: int, subject: str, message: str) -> bool:
    return False


def get_client_conversations() -> List[Dict[str, Any]]:
    return []


def get_client_conversation(user_id: int) -> List[Dict[str, Any]]:
    return []


def mark_client_conversation_read(user_id: int) -> bool:
    return False


def count_unread_client_conversations() -> int:
    return 0


def get_shop_conversations() -> List[Dict[str, Any]]:
    return []


def get_shop_conversation(shop_id: int) -> List[Dict[str, Any]]:
    return []


def mark_shop_conversation_read(shop_id: int) -> bool:
    return False


def count_unread_shop_conversations() -> int:
    return 0


def get_daily_orders_stats(days: int = 30) -> List[Dict[str, Any]]:
    return []


def get_popular_products(limit: int = 10) -> List[Dict[str, Any]]:
    return []


def get_monthly_stats() -> List[Dict[str, Any]]:
    return []


def get_shop_monthly_stats(shop_id: int) -> List[Dict[str, Any]]:
    return []


def log_activity(user_id: int, user_name: str, action: str, details: str = "", ip_address: str = "") -> bool:
    return True


def get_activity_log(limit: int = 100) -> List[Dict[str, Any]]:
    return []


def record_login_attempt(email: str, success: bool, ip_address: str = "") -> bool:
    return True


def is_account_locked(email: str) -> Tuple[bool, int]:
    return False, 0


def count_shop_products(shop_id: int) -> int:
    return len(list_shop_products(shop_id))


def count_shop_orders(shop_id: int) -> int:
    return 0


def get_shop_revenue(shop_id: int) -> float:
    return 0.0


def list_shop_orders(shop_id: int) -> List[Dict[str, Any]]:
    return []


def delete_product_by_owner(product_id: int, owner_user_id: int) -> Tuple[bool, str]:
    return False, "Non disponible en ligne."


def update_order_status_if_shop(order_id: int, shop_id: int, status: str) -> bool:
    return False


def list_shop_orders_anonymous(shop_id: int) -> List[Dict[str, Any]]:
    return []


def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    return []


def get_all_shops_for_admin() -> List[Dict[str, Any]]:
    return list_all_shops()
