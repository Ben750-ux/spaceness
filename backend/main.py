import asyncio
import os
import uuid
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
import crud as db
from models import init_db

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


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

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


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


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str


class AppVersionResponse(BaseModel):
    latest_version: str = "1.0.0"
    min_version: str = "1.0.0"
    download_url: str = ""
    update_message: str = ""


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


class StatusUpdateRequest(BaseModel):
    status: str


class BlockUserRequest(BaseModel):
    user_id: int
    blocked: int


class ReplyMessageRequest(BaseModel):
    message_id: int
    reply: str


class MarkReadRequest(BaseModel):
    message_id: int


class AppSettingsRequest(BaseModel):
    is_blocked: int
    block_message: str = ""


class ShopCredentialsRequest(BaseModel):
    owner_name: str = ""
    password: str = ""


class ShopInfoRequest(BaseModel):
    shop_name: str = ""
    description: str = ""
    contact_info: str = ""


class MessageToShopRequest(BaseModel):
    subject: str
    message: str


class VendorMessageReplyRequest(BaseModel):
    reply: str


class VendorLoginRequest(BaseModel):
    email: str
    password: str


class VendorShopUpdateRequest(BaseModel):
    shop_name: str = ""
    description: str = ""
    contact_info: str = ""
    logo_url: str = ""
    banner_url: str = ""


class VendorProductAddRequest(BaseModel):
    name: str
    category: str = "General"
    price: float
    stock: int
    description: str = ""
    image_url: str = ""


class VendorProductUpdateRequest(BaseModel):
    stock: int
    is_active: int = 1


class VendorOrderStatusRequest(BaseModel):
    status: str


class VendorMessageRequest(BaseModel):
    subject: str
    message: str


class ShopCreateRequest(BaseModel):
    owner_user_id: int
    shop_name: str
    description: str = ""
    contact_info: str = ""


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


# ============ MOT DE PASSE OUBLIE ============
@app.post("/api/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    ok, code = await db.forgot_password(req.email)
    if not ok:
        raise HTTPException(status_code=404, detail=code)
    return {"ok": True, "code": code}

@app.post("/api/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    ok, msg = await db.reset_password(req.email, req.code, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}

# ============ VERSION APP ============
@app.get("/api/app-version")
async def get_app_version():
    return {
        "ok": True,
        "latest_version": "1.0.1",
        "min_version": "1.0.0",
        "download_url": "",
        "update_message": "",
    }


# ============ UPLOAD ============
@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Format non autorise: {ext}. Utilisez jpg, png, gif, webp, bmp.")
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    url = f"/uploads/{filename}"
    return {"ok": True, "url": url, "filename": filename}


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


@app.post("/api/shops/create")
async def create_shop(req: ShopCreateRequest):
    ok, msg = await db.create_shop(req.owner_user_id, req.shop_name, req.description, req.contact_info)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


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


@app.delete("/api/admin/products/{product_id}")
async def admin_delete_product(product_id: int):
    ok = await db.delete_product(product_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur suppression produit")
    return {"ok": True}


@app.delete("/api/admin/shops/{shop_id}")
async def admin_delete_shop(shop_id: int):
    ok = await db.delete_shop(shop_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur suppression boutique")
    return {"ok": True}


@app.get("/api/admin/shops/{shop_id}/details")
async def admin_get_shop_details(shop_id: int):
    shop = await db.get_shop_with_owner(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return {"ok": True, "shop": shop}


@app.put("/api/admin/shops/{shop_id}/credentials")
async def admin_update_shop_credentials(shop_id: int, req: ShopCredentialsRequest):
    ok, msg = await db.update_shop_credentials(shop_id, req.owner_name, req.password)
    return {"ok": ok, "message": msg}


@app.put("/api/admin/shops/{shop_id}/info")
async def admin_update_shop_info(shop_id: int, req: ShopInfoRequest):
    ok, msg = await db.update_shop_info(shop_id, req.shop_name, req.description, req.contact_info)
    return {"ok": ok, "message": msg}


@app.get("/api/admin/vendor-messages")
async def admin_get_all_vendor_messages():
    messages = await db.get_all_vendor_admin_messages()
    return {"ok": True, "messages": messages}


@app.post("/api/admin/vendor-messages/{message_id}/reply")
async def admin_reply_vendor_message(message_id: int, req: VendorMessageReplyRequest):
    ok = await db.reply_vendor_message(message_id, req.reply)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur reponse")
    return {"ok": True}


@app.post("/api/admin/shops/{shop_id}/message")
async def admin_send_message_to_shop(shop_id: int, req: MessageToShopRequest):
    ok = await db.send_message_to_shop(shop_id, req.subject, req.message)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur envoi message")
    return {"ok": True}


@app.get("/api/admin/activity-log")
async def admin_get_activity_log(limit: int = 100):
    logs = await db.get_activity_log(limit)
    return {"ok": True, "logs": logs}


@app.get("/api/admin/stats/advanced")
async def admin_get_advanced_stats(days: int = 30):
    daily_orders, popular_products, monthly_stats = await asyncio.gather(
        db.get_daily_orders_stats(days),
        db.get_popular_products(10),
        db.get_monthly_stats(),
    )
    return {
        "ok": True,
        "daily_orders": [dict(d) for d in daily_orders],
        "popular_products": [dict(p) for p in popular_products],
        "monthly_stats": [dict(m) for m in monthly_stats],
    }


@app.get("/api/admin/conversations/clients")
async def admin_get_client_conversations():
    conversations = await db.get_client_conversations()
    return {"ok": True, "conversations": conversations}


@app.get("/api/admin/conversations/clients/{user_id}")
async def admin_get_client_conversation(user_id: int):
    messages = await db.get_user_messages(user_id)
    return {"ok": True, "messages": messages}


@app.get("/api/admin/conversations/shops")
async def admin_get_shop_conversations():
    conversations = await db.get_shop_conversations()
    return {"ok": True, "conversations": conversations}


@app.get("/api/admin/conversations/shops/{shop_id}")
async def admin_get_shop_conversation(shop_id: int):
    messages = await db.get_vendor_messages(shop_id)
    return {"ok": True, "messages": messages}


@app.get("/api/admin/shops/list-all")
async def admin_list_all_shops():
    shops = await db.list_all_shops()
    return {"ok": True, "shops": shops}


# ============ VENDOR API ============
@app.post("/api/vendor/login")
async def vendor_login(req: VendorLoginRequest):
    ok, msg, vendor = await db.login_vendor(req.email, req.password)
    if not ok:
        raise HTTPException(status_code=401, detail=msg)
    return {"ok": True, "vendor": vendor}


@app.get("/api/vendor/stats")
async def vendor_get_stats(shop_id: int):
    products, orders, revenue, subscribers = await asyncio.gather(
        db.count_shop_products(shop_id),
        db.count_shop_orders(shop_id),
        db.get_shop_revenue(shop_id),
        db.get_shop_subscriber_count(shop_id),
    )
    return {
        "ok": True,
        "total_products": products,
        "total_orders": orders,
        "total_revenue": revenue,
        "total_subscribers": subscribers,
    }


@app.get("/api/vendor/stats/monthly")
async def vendor_get_monthly_stats(shop_id: int):
    stats = await db.get_shop_monthly_stats(shop_id)
    return {"ok": True, "stats": [dict(s) for s in stats]}


@app.get("/api/vendor/shop")
async def vendor_get_shop(owner_user_id: int):
    shop = await db.get_shop_by_owner(owner_user_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return {"ok": True, "shop": shop}


@app.put("/api/vendor/shop")
async def vendor_update_shop(owner_user_id: int, req: VendorShopUpdateRequest):
    shop = await db.get_shop_by_owner(owner_user_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    ok, msg = await db.update_shop(owner_user_id, req.shop_name, req.description, req.contact_info, req.logo_url, req.banner_url)
    return {"ok": ok, "message": msg}


@app.get("/api/vendor/products")
async def vendor_get_products(shop_id: int):
    products = await db.list_shop_products(shop_id)
    return {"ok": True, "products": products}


@app.post("/api/vendor/products")
async def vendor_add_product(owner_user_id: int, req: VendorProductAddRequest):
    ok, msg = await db.add_product(owner_user_id, req.name, req.category, req.price, req.stock, req.description, req.image_url)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": msg}


@app.put("/api/vendor/products/{product_id}")
async def vendor_update_product(product_id: int, owner_user_id: int, req: VendorProductUpdateRequest):
    ok, msg = await db.update_product_stock(product_id, owner_user_id, req.stock, req.is_active)
    return {"ok": ok, "message": msg}


@app.delete("/api/vendor/products/{product_id}")
async def vendor_delete_product(product_id: int, owner_user_id: int):
    ok, msg = await db.delete_product_by_owner(product_id, owner_user_id)
    return {"ok": ok, "message": msg}


@app.get("/api/vendor/orders")
async def vendor_get_orders(shop_id: int):
    orders = await db.list_shop_orders_anonymous(shop_id)
    return {"ok": True, "orders": orders}


@app.put("/api/vendor/orders/{order_id}/status")
async def vendor_update_order_status(order_id: int, shop_id: int, req: VendorOrderStatusRequest):
    ok = await db.update_order_status_if_shop(order_id, shop_id, req.status)
    return {"ok": ok}


@app.get("/api/vendor/messages")
async def vendor_get_messages(shop_id: int):
    messages = await db.get_vendor_messages(shop_id)
    return {"ok": True, "messages": messages}


@app.post("/api/vendor/messages")
async def vendor_send_message(shop_id: int, req: VendorMessageRequest):
    ok = await db.send_vendor_message(shop_id, req.subject, req.message)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur envoi message")
    return {"ok": True}


@app.put("/api/admin/orders/{order_id}/status")
async def admin_update_order_status(order_id: int, req: StatusUpdateRequest):
    ok = await db.update_order_status(order_id, req.status)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur mise a jour statut")
    return {"ok": True}


@app.get("/api/admin/users/{user_id}/orders")
async def admin_get_user_orders(user_id: int):
    orders = await db.get_user_orders(user_id)
    return {"ok": True, "orders": orders}


@app.get("/api/admin/users/{user_id}/subscriptions")
async def admin_get_user_subscriptions(user_id: int):
    subs = await db.get_user_subscriptions(user_id)
    return {"ok": True, "subscriptions": subs}


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
async def set_app_settings(req: AppSettingsRequest):
    ok = await db.set_app_blocked(req.is_blocked, req.block_message)
    if not ok:
        raise HTTPException(status_code=400, detail="Erreur")
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

# deploy trigger 2026-06-22 11:13:06
