from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
import crud as db
from models import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await db.seed_default_settings()
    await db.seed_admin_and_demo()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ MODELS ============
class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "client"


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyCodeRequest(BaseModel):
    user_id: int
    code: str


class ResendCodeRequest(BaseModel):
    user_id: int


class UserIdRequest(BaseModel):
    user_id: int


class SaveCodeRequest(BaseModel):
    user_id: int
    code: str


class ProductAddRequest(BaseModel):
    owner_user_id: int
    name: str
    category: str = "General"
    price: float
    stock: int
    description: str = ""
    image_url: str = ""


class ProductUpdateRequest(BaseModel):
    product_id: int
    owner_user_id: int
    stock: int
    is_active: int


class OrderRequest(BaseModel):
    client_user_id: int
    product_id: int
    quantity: int


class ReviewRequest(BaseModel):
    user_id: int
    product_id: int
    rating: int
    comment: str = ""


class FavoriteRequest(BaseModel):
    user_id: int
    product_id: int


class ShopUpdateRequest(BaseModel):
    owner_user_id: int
    shop_name: str
    description: str = ""
    contact_info: str = ""
    logo_url: str = ""
    banner_url: str = ""


class SubscribeRequest(BaseModel):
    client_user_id: int
    shop_id: int


class MessageRequest(BaseModel):
    user_id: int
    subject: str
    message: str


class OrderStatusRequest(BaseModel):
    order_id: int
    status: str


class BlockUserRequest(BaseModel):
    user_id: int
    blocked: int


class ReplyMessageRequest(BaseModel):
    message_id: int
    reply: str


class MarkReadRequest(BaseModel):
    message_id: int


# ============ AUTH ============
@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    ok, msg = await db.create_user(req.full_name, req.email, req.password, req.role)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    _, _, user = await db.login_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=500, detail="Erreur lors de la creation du compte")
    return {"ok": True, "message": msg, "user_id": user.get("id")}


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    ok, msg, user = await db.login_user(req.email, req.password)
    if not ok and msg == "VERIFICATION_REQUIRED":
        return {"ok": False, "message": msg, "verification_required": True, "user": user}
    if not ok:
        raise HTTPException(status_code=401, detail=msg)
    return {"ok": True, "message": msg, "user": user}


@app.post("/api/auth/verify-code")
async def verify_code(req: VerifyCodeRequest):
    ok, msg = await db.verify_email_code(req.user_id, req.code)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    user = await db.get_user_by_id(req.user_id)
    return {"ok": True, "message": msg, "user": user}


@app.post("/api/auth/resend-code")
async def resend_code(req: ResendCodeRequest):
    user = await db.get_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    code = db._generate_verification_code()
    await db.save_verification_code(req.user_id, code)
    return {"ok": True, "code": code, "email": user["email"]}


@app.post("/api/auth/save-code")
async def save_code(req: SaveCodeRequest):
    await db.save_verification_code(req.user_id, req.code)
    return {"ok": True}


@app.post("/api/auth/get-user")
async def get_user(req: UserIdRequest):
    user = await db.get_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {"ok": True, "user": user}


# ============ PRODUITS ============
@app.get("/api/products")
async def list_products(search: str = "", category: str = ""):
    products = await db.list_market_products(search, category)
    return {"ok": True, "products": products}


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    product = await db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return {"ok": True, "product": product}


@app.get("/api/shops/{shop_id}/products")
async def list_shop_products(shop_id: int):
    products = await db.list_shop_products(shop_id)
    return {"ok": True, "products": products}


@app.post("/api/products/add")
async def add_product(req: ProductAddRequest):
    ok, msg = await db.add_product(
        req.owner_user_id, req.name, req.category, req.price,
        req.stock, req.description, req.image_url,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


@app.post("/api/products/update-stock")
async def update_product_stock(req: ProductUpdateRequest):
    ok, msg = await db.update_product_stock(
        req.product_id, req.owner_user_id, req.stock, req.is_active
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


# ============ BOUTIQUES ============
@app.get("/api/shops/{shop_id}")
async def get_shop(shop_id: int):
    shop = await db.get_shop_details(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return {"ok": True, "shop": shop}


@app.post("/api/shops/update")
async def update_shop(req: ShopUpdateRequest):
    ok, msg = await db.update_shop(
        req.owner_user_id, req.shop_name, req.description,
        req.contact_info, req.logo_url, req.banner_url,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


# ============ COMMANDES ============
@app.post("/api/orders/place")
async def place_order(req: OrderRequest):
    ok, msg = await db.place_order(req.client_user_id, req.product_id, req.quantity)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


@app.get("/api/orders/client/{client_user_id}")
async def list_client_orders(client_user_id: int):
    orders = await db.list_orders_for_client(client_user_id)
    return {"ok": True, "orders": orders}


@app.post("/api/orders/update-status")
async def update_order_status(req: OrderStatusRequest):
    ok = await db.update_order_status(req.order_id, req.status)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur mise a jour commande")
    return {"ok": True, "message": "Statut mis a jour"}


# ============ FAVORIS ============
@app.post("/api/favorites/add")
async def add_favorite(req: FavoriteRequest):
    ok = await db.add_to_favorites(req.user_id, req.product_id)
    return {"ok": ok}


@app.post("/api/favorites/remove")
async def remove_favorite(req: FavoriteRequest):
    ok = await db.remove_from_favorites(req.user_id, req.product_id)
    return {"ok": ok}


@app.post("/api/favorites/check")
async def check_favorite(req: FavoriteRequest):
    is_fav = await db.is_favorite(req.user_id, req.product_id)
    return {"ok": True, "is_favorite": is_fav}


@app.get("/api/favorites/{user_id}")
async def list_favorites(user_id: int):
    favorites = await db.list_favorites(user_id)
    return {"ok": True, "favorites": favorites}


# ============ HISTORIQUE ============
@app.get("/api/history/{user_id}")
async def list_history(user_id: int):
    history = await db.list_history(user_id)
    return {"ok": True, "history": history}


@app.post("/api/history/add")
async def add_history(req: FavoriteRequest):
    await db.add_to_history(req.user_id, req.product_id)
    return {"ok": True}


@app.post("/api/history/clear")
async def clear_history(req: UserIdRequest):
    await db.clear_history(req.user_id)
    return {"ok": True}


# ============ AVIS ============
@app.post("/api/reviews/add")
async def add_review(req: ReviewRequest):
    ok = await db.add_review(req.user_id, req.product_id, req.rating, req.comment)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur ajout avis")
    return {"ok": True, "message": "Avis ajoute"}


@app.get("/api/reviews/{product_id}")
async def get_reviews(product_id: int):
    reviews = await db.get_product_reviews(product_id)
    rating, count = await db.get_product_rating(product_id)
    return {"ok": True, "reviews": reviews, "rating": rating, "count": count}


# ============ ABONNEMENTS ============
@app.post("/api/subscriptions/subscribe")
async def subscribe(req: SubscribeRequest):
    ok = await db.subscribe_to_shop(req.client_user_id, req.shop_id)
    return {"ok": ok}


@app.post("/api/subscriptions/unsubscribe")
async def unsubscribe(req: SubscribeRequest):
    ok = await db.unsubscribe_from_shop(req.client_user_id, req.shop_id)
    return {"ok": ok}


@app.get("/api/subscriptions/{user_id}")
async def list_subscriptions(user_id: int):
    shops = await db.list_subscribed_shops(user_id)
    return {"ok": True, "shops": shops}


@app.get("/api/subscriptions/{user_id}/products")
async def get_subscribed_products(user_id: int):
    products = await db.get_subscribed_shop_products(user_id)
    return {"ok": True, "products": products}


# ============ ADMIN / UTILISATEURS ============
@app.get("/api/admin/users")
async def list_users():
    users = await db.list_all_users()
    return {"ok": True, "users": users}


@app.post("/api/admin/users/block")
async def block_user(req: BlockUserRequest):
    ok, msg = await db.set_user_block_status(req.user_id, req.blocked)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


@app.post("/api/admin/users/delete")
async def delete_user(req: UserIdRequest):
    ok, msg = await db.delete_user(req.user_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


@app.get("/api/admin/stats")
async def get_stats():
    users, products, orders, shops = await asyncio.gather(
        db.count_users(), db.count_products(), db.count_orders(), db.count_shops(),
    )
    return {"ok": True, "users": users, "products": products, "orders": orders, "shops": shops}


@app.get("/api/admin/orders")
async def get_all_orders():
    orders = await db.list_all_orders()
    return {"ok": True, "orders": orders}


@app.get("/api/admin/products")
async def get_all_products():
    products = await db.list_all_products()
    return {"ok": True, "products": products}


@app.get("/api/admin/shops")
async def get_all_shops():
    shops = await db.list_all_shops()
    return {"ok": True, "shops": shops}


# ============ MESSAGES ============
@app.post("/api/messages/send")
async def send_message(req: MessageRequest):
    ok = await db.send_admin_message(req.user_id, req.subject, req.message)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur envoi message")
    return {"ok": True}


@app.get("/api/messages/{user_id}")
async def get_messages(user_id: int):
    messages = await db.get_user_messages(user_id)
    return {"ok": True, "messages": messages}


@app.get("/api/admin/messages")
async def get_all_messages():
    messages = await db.get_all_messages()
    return {"ok": True, "messages": messages}


@app.post("/api/admin/messages/reply")
async def reply_message(req: ReplyMessageRequest):
    ok = await db.reply_to_message(req.message_id, req.reply)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur reponse")
    return {"ok": True}


@app.post("/api/admin/messages/read")
async def mark_read(req: MarkReadRequest):
    ok = await db.mark_message_read(req.message_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur")
    return {"ok": True}


@app.get("/api/admin/messages/unread-count")
async def unread_count():
    count = await db.count_unread_messages()
    return {"ok": True, "count": count}


# ============ PARAMÈTRES APP ============
@app.get("/api/app-settings")
async def get_app_settings():
    settings = await db.get_app_settings()
    return {"ok": True, "settings": settings}


@app.post("/api/app-settings")
async def set_app_settings(is_blocked: bool, block_message: str = ""):
    ok = await db.set_app_blocked(is_blocked, block_message)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur")
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
