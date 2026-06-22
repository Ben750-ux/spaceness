import hashlib
import os
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    AdminMessage, AppSetting, Favorite, LoginAttempt, Order, Product,
    ProductReview, Shop, ShopSubscription, User, UserRole, ViewHistory,
    VendorAdminMessage, async_session,
)


# ============ HELPERS ============
def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return salt, digest


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, digest = _hash_password(password, salt)
    return digest == password_hash


def _generate_verification_code() -> str:
    return str(random.randint(100000, 999999))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def _ensure_default_settings(session: AsyncSession):
    result = await session.execute(select(AppSetting).where(AppSetting.id == 1))
    if not result.scalar_one_or_none():
        session.add(AppSetting(id=1, is_blocked=0, block_message=""))


# ============ AUTH ============
async def create_user(full_name: str, email: str, password: str, role: str) -> Tuple[bool, str]:
    if role not in {"client", "boutique"}:
        return False, "Role invalide."
    if len(password) < 6:
        return False, "Le mot de passe doit avoir au moins 6 caracteres."
    try:
        async with async_session() as session:
            salt, pwd_hash = _hash_password(password)
            user = User(
                full_name=full_name.strip(),
                email=email.strip().lower(),
                password_hash=pwd_hash,
                password_salt=salt,
                role=UserRole(role),
            )
            session.add(user)
            await session.flush()
            if role == "boutique":
                shop = Shop(
                    owner_user_id=user.id,
                    shop_name=f"{full_name.strip()} Shop",
                    description="",
                    contact_info="",
                )
                session.add(shop)
            await session.commit()
        return True, "Compte cree avec succes."
    except Exception:
        return False, "Cet email est deja utilise."


async def login_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == email.strip().lower())
        )
        row = result.scalar_one_or_none()
        if not row:
            return False, "Email ou mot de passe incorrect.", None
        if row.is_blocked:
            return False, "Compte bloque par l'administration.", None
        if not verify_password(password, row.password_salt, row.password_hash):
            return False, "Email ou mot de passe incorrect.", None
        if not row.is_verified:
            return False, "VERIFICATION_REQUIRED", {
                "id": row.id, "email": row.email, "full_name": row.full_name
            }
        return True, "Connexion reussie.", {
            "id": row.id,
            "full_name": row.full_name,
            "email": row.email,
            "role": row.role.value,
        }


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        row = result.scalar_one_or_none()
        if not row or row.is_blocked:
            return None
        return {
            "id": row.id,
            "full_name": row.full_name,
            "email": row.email,
            "role": row.role.value,
            "is_verified": bool(row.is_verified),
        }


async def save_verification_code(user_id: int, code: str) -> None:
    expires = (_now() + timedelta(minutes=10)).isoformat()
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(verification_code=code, verification_code_expires=expires)
        )
        await session.commit()


async def verify_email_code(user_id: int, code: str) -> Tuple[bool, str]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return False, "Utilisateur introuvable."
        if not row.verification_code:
            return False, "Aucun code de verification trouve."
        if row.verification_code != code:
            return False, "Code incorrect."
        expires = datetime.fromisoformat(row.verification_code_expires)
        if _now() > expires:
            return False, "Code expire. Demandez un nouveau code."
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=1, verification_code=None, verification_code_expires=None)
        )
        await session.commit()
        return True, "Email verifie avec succes !"


async def is_user_verified(user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(User.is_verified).where(User.id == user_id)
        )
        row = result.scalar_one_or_none()
        return bool(row)


# ============ SHOPS ============
async def get_shop_by_owner(owner_user_id: int) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(Shop).where(Shop.owner_user_id == owner_user_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {c.name: getattr(row, c.name) for c in Shop.__table__.columns}


async def get_shop_details(shop_id: int) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(select(Shop).where(Shop.id == shop_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {c.name: getattr(row, c.name) for c in Shop.__table__.columns}


async def update_shop(
    owner_user_id: int, shop_name: str, description: str = "",
    contact_info: str = "", logo_url: str = "", banner_url: str = "",
) -> Tuple[bool, str]:
    try:
        async with async_session() as session:
            result = await session.execute(
                update(Shop)
                .where(Shop.owner_user_id == owner_user_id)
                .values(
                    shop_name=shop_name.strip(),
                    description=description.strip(),
                    contact_info=contact_info.strip(),
                    logo_url=logo_url.strip(),
                    banner_url=banner_url.strip(),
                )
            )
            if result.rowcount == 0:
                return False, "Boutique introuvable."
            await session.commit()
        return True, "Profil boutique mis a jour."
    except Exception:
        return False, "Nom de boutique deja utilise."


# ============ PRODUCTS ============
async def add_product(
    owner_user_id: int, name: str, category: str, price: float,
    stock: int, description: str = "", image_url: str = "",
) -> Tuple[bool, str]:
    shop = await get_shop_by_owner(owner_user_id)
    if not shop:
        return False, "Boutique introuvable."
    async with async_session() as session:
        product = Product(
            shop_id=shop["id"],
            name=name.strip(),
            category=category.strip() or "General",
            price=price,
            stock=stock,
            description=description.strip(),
            image_url=image_url.strip(),
        )
        session.add(product)
        await session.commit()
    return True, "Produit ajoute."


async def update_product_stock(
    product_id: int, owner_user_id: int, stock: int, is_active: int,
) -> Tuple[bool, str]:
    async with async_session() as session:
        result = await session.execute(
            select(Product).join(Shop).where(
                Product.id == product_id,
                Shop.owner_user_id == owner_user_id,
            )
        )
        product = result.scalar_one_or_none()
        if not product:
            return False, "Produit introuvable."
        product.stock = stock
        product.is_active = is_active
        await session.commit()
    return True, "Produit mis a jour."


async def list_shop_products(shop_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(Product)
            .where(Product.shop_id == shop_id)
            .order_by(Product.id.desc())
        )
        rows = result.scalars().all()
        return [{c.name: getattr(r, c.name) for c in Product.__table__.columns} for r in rows]


async def list_market_products(search: str = "", category: str = "") -> List[Dict[str, Any]]:
    search = search.strip().lower()
    category = category.strip().lower()
    query = (
        select(
            Product.id, Product.name, Product.category, Product.price,
            Product.stock, Product.description, Product.image_url,
            Product.image_url_2, Product.image_url_3,
            Shop.id.label("shop_id"), Shop.shop_name,
        )
        .join(Shop, Product.shop_id == Shop.id)
        .where(Product.is_active == 1, Product.stock > 0)
    )
    if search:
        query = query.where(
            (func.lower(Product.name).like(f"%{search}%")) |
            (func.lower(Shop.shop_name).like(f"%{search}%"))
        )
    if category:
        query = query.where(func.lower(Product.category) == category)
    query = query.order_by(Product.id.desc())

    async with async_session() as session:
        result = await session.execute(query)
        rows = result.all()
        return [dict(r._mapping) for r in rows]


async def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(
                Product.id, Product.name, Product.category, Product.price,
                Product.stock, Product.description, Product.image_url,
                Product.image_url_2, Product.image_url_3, Product.is_active,
                Shop.id.label("shop_id"), Shop.shop_name,
            )
            .join(Shop, Product.shop_id == Shop.id)
            .where(Product.id == product_id)
        )
        result = await session.execute(query)
        row = result.one_or_none()
        return dict(row._mapping) if row else None


# ============ ORDERS ============
async def place_order(
    client_user_id: int, product_id: int, quantity: int,
) -> Tuple[bool, str]:
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            return False, "Produit introuvable."
        if not product.is_active or product.stock <= 0:
            return False, "Produit indisponible."
        if quantity <= 0:
            return False, "Quantite invalide."
        if product.stock < quantity:
            return False, "Stock insuffisant."
        total = float(product.price) * quantity
        order = Order(
            client_user_id=client_user_id,
            product_id=product_id,
            quantity=quantity,
            total_amount=total,
            status="pending",
        )
        session.add(order)
        product.stock -= quantity
        await session.commit()
    return True, "Commande enregistree."


async def list_orders_for_client(client_user_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(
                Order.id, Order.quantity, Order.total_amount, Order.status,
                Order.created_at,
                Product.id.label("product_id"), Product.name.label("product_name"),
                Product.description.label("product_description"),
                Product.price.label("product_price"),
                Product.image_url.label("product_image_url"),
                Product.image_url_2.label("product_image_url_2"),
                Product.image_url_3.label("product_image_url_3"),
                Product.category.label("product_category"),
                Shop.id.label("shop_id"), Shop.shop_name, Shop.logo_url.label("shop_logo_url"),
            )
            .join(Product, Order.product_id == Product.id)
            .join(Shop, Product.shop_id == Shop.id)
            .where(Order.client_user_id == client_user_id)
            .order_by(Order.id.desc())
        )
        result = await session.execute(query)
        return [dict(r._mapping) for r in result.all()]


async def update_order_status(order_id: int, status: str) -> bool:
    try:
        async with async_session() as session:
            await session.execute(
                update(Order).where(Order.id == order_id).values(status=status)
            )
            await session.commit()
        return True
    except Exception:
        return False


# ============ FAVORITES ============
async def add_to_favorites(user_id: int, product_id: int) -> bool:
    try:
        async with async_session() as session:
            fav = Favorite(user_id=user_id, product_id=product_id)
            session.add(fav)
            await session.commit()
        return True
    except Exception:
        return False


async def remove_from_favorites(user_id: int, product_id: int) -> bool:
    async with async_session() as session:
        await session.execute(
            delete(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.product_id == product_id,
            )
        )
        await session.commit()
    return True


async def is_favorite(user_id: int, product_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Favorite.id).where(
                Favorite.user_id == user_id,
                Favorite.product_id == product_id,
            )
        )
        return result.scalar_one_or_none() is not None


async def list_favorites(user_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(
                Product.id, Product.name, Product.category, Product.price,
                Product.stock, Product.description, Product.image_url,
                Product.image_url_2, Product.image_url_3,
                Shop.id.label("shop_id"), Shop.shop_name,
                Favorite.created_at.label("favorited_at"),
            )
            .join(Favorite, Product.id == Favorite.product_id)
            .join(Shop, Product.shop_id == Shop.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        result = await session.execute(query)
        return [dict(r._mapping) for r in result.all()]


# ============ HISTORY ============
async def add_to_history(user_id: int, product_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            delete(ViewHistory).where(
                ViewHistory.user_id == user_id,
                ViewHistory.product_id == product_id,
            )
        )
        session.add(ViewHistory(user_id=user_id, product_id=product_id))
        # Keep only last 50
        subq = (
            select(ViewHistory.id)
            .where(ViewHistory.user_id == user_id)
            .order_by(ViewHistory.viewed_at.desc())
            .limit(50)
            .subquery()
        )
        await session.execute(
            delete(ViewHistory).where(
                ViewHistory.user_id == user_id,
                ViewHistory.id.notin_(select(subq.c.id)),
            )
        )
        await session.commit()


async def list_history(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(
                Product.id, Product.name, Product.category, Product.price,
                Product.stock, Product.description, Product.image_url,
                Product.image_url_2, Product.image_url_3,
                Shop.id.label("shop_id"), Shop.shop_name,
                ViewHistory.viewed_at,
            )
            .join(ViewHistory, Product.id == ViewHistory.product_id)
            .join(Shop, Product.shop_id == Shop.id)
            .where(ViewHistory.user_id == user_id)
            .order_by(ViewHistory.viewed_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return [dict(r._mapping) for r in result.all()]


async def clear_history(user_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            delete(ViewHistory).where(ViewHistory.user_id == user_id)
        )
        await session.commit()


# ============ REVIEWS ============
async def add_review(user_id: int, product_id: int, rating: int, comment: str = "") -> bool:
    if not 1 <= rating <= 5:
        return False
    async with async_session() as session:
        try:
            existing = await session.execute(
                select(ProductReview).where(
                    ProductReview.user_id == user_id,
                    ProductReview.product_id == product_id,
                )
            )
            review = existing.scalar_one_or_none()
            if review:
                review.rating = rating
                review.comment = comment
            else:
                session.add(
                    ProductReview(user_id=user_id, product_id=product_id, rating=rating, comment=comment)
                )
            await session.commit()
            return True
        except Exception:
            return False


async def get_product_reviews(product_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(ProductReview, User.full_name.label("user_name"))
            .join(User, ProductReview.user_id == User.id)
            .where(ProductReview.product_id == product_id)
            .order_by(ProductReview.created_at.desc())
        )
        result = await session.execute(query)
        rows = []
        for r in result.all():
            d = {c.name: getattr(r.ProductReview, c.name) for c in ProductReview.__table__.columns}
            d["user_name"] = r.user_name
            rows.append(d)
        return rows


async def get_product_rating(product_id: int) -> Tuple[float, int]:
    async with async_session() as session:
        result = await session.execute(
            select(
                func.avg(ProductReview.rating).label("avg_rating"),
                func.count(ProductReview.id).label("count"),
            ).where(ProductReview.product_id == product_id)
        )
        row = result.one()
        avg = row.avg_rating if row.avg_rating else 0.0
        count = row.count or 0
        return (round(float(avg), 1), count)


# ============ SUBSCRIPTIONS ============
async def is_subscribed_to_shop(client_user_id: int, shop_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(ShopSubscription.id).where(
                ShopSubscription.client_user_id == client_user_id,
                ShopSubscription.shop_id == shop_id,
            )
        )
        return result.scalar_one_or_none() is not None


async def subscribe_to_shop(client_user_id: int, shop_id: int) -> bool:
    try:
        async with async_session() as session:
            sub = ShopSubscription(client_user_id=client_user_id, shop_id=shop_id)
            session.add(sub)
            await session.commit()
        return True
    except Exception:
        return False


async def unsubscribe_from_shop(client_user_id: int, shop_id: int) -> bool:
    async with async_session() as session:
        await session.execute(
            delete(ShopSubscription).where(
                ShopSubscription.client_user_id == client_user_id,
                ShopSubscription.shop_id == shop_id,
            )
        )
        await session.commit()
    return True


async def get_shop_subscriber_count(shop_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(ShopSubscription.id)).where(
                ShopSubscription.shop_id == shop_id
            )
        )
        return result.scalar() or 0


async def list_subscribed_shops(client_user_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(Shop.id, Shop.shop_name, Shop.logo_url, Shop.description,
                   ShopSubscription.subscribed_at)
            .join(ShopSubscription, Shop.id == ShopSubscription.shop_id)
            .where(ShopSubscription.client_user_id == client_user_id)
            .order_by(ShopSubscription.subscribed_at.desc())
        )
        result = await session.execute(query)
        return [dict(r._mapping) for r in result.all()]


async def get_subscribed_shop_products(client_user_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(Product, Shop.shop_name, Shop.logo_url.label("shop_logo_url"),
                   text("1 AS is_subscribed"))
            .join(Shop, Product.shop_id == Shop.id)
            .join(ShopSubscription, Shop.id == ShopSubscription.shop_id)
            .where(
                ShopSubscription.client_user_id == client_user_id,
                Product.is_active == 1,
            )
            .order_by(Product.id.desc())
        )
        result = await session.execute(query)
        return [dict(r._mapping) for r in result.all()]


# ============ ADMIN ============
async def list_all_users() -> List[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(
                User.id, User.full_name, User.email, User.role,
                User.is_blocked, User.created_at,
            )
            .order_by(User.id.desc())
        )
        return [dict(r._mapping) for r in result.all()]


async def set_user_block_status(user_id: int, blocked: int) -> Tuple[bool, str]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        row = result.scalar_one_or_none()
        if not row:
            return False, "Utilisateur introuvable."
        if row.role == UserRole.admin:
            return False, "Impossible de bloquer un administrateur."
        row.is_blocked = blocked
        await session.commit()
    return True, "Statut utilisateur mis a jour."


async def delete_user(user_id: int) -> Tuple[bool, str]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        row = result.scalar_one_or_none()
        if not row:
            return False, "Utilisateur introuvable."
        if row.role == UserRole.admin:
            return False, "Suppression d'admin non autorisee."
        await session.delete(row)
        await session.commit()
    return True, "Utilisateur supprime."


async def count_users() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar() or 0


async def count_products() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Product.id)))
        return result.scalar() or 0


async def count_orders() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Order.id)))
        return result.scalar() or 0


async def count_shops() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Shop.id)))
        return result.scalar() or 0


async def list_all_products() -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(Product, Shop.shop_name)
            .join(Shop, Product.shop_id == Shop.id)
            .order_by(Product.id.desc())
        )
        result = await session.execute(query)
        rows = []
        for r in result.all():
            d = {c.name: getattr(r.Product, c.name) for c in Product.__table__.columns}
            d["shop_name"] = r.shop_name
            rows.append(d)
        return rows


async def list_all_shops() -> List[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(select(Shop).order_by(Shop.id.desc()))
        rows = result.scalars().all()
        return [{c.name: getattr(r, c.name) for c in Shop.__table__.columns} for r in rows]


async def list_all_orders() -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(
                Order, Product.name.label("product_name"),
                User.full_name.label("client_name"), Shop.shop_name,
            )
            .join(Product, Order.product_id == Product.id)
            .join(User, Order.client_user_id == User.id)
            .join(Shop, Product.shop_id == Shop.id)
            .order_by(Order.id.desc())
        )
        result = await session.execute(query)
        rows = []
        for r in result.all():
            d = {c.name: getattr(r.Order, c.name) for c in Order.__table__.columns}
            d["product_name"] = r.product_name
            d["client_name"] = r.client_name
            d["shop_name"] = r.shop_name
            rows.append(d)
        return rows


async def toggle_user_block(user_id: int, blocked: bool) -> bool:
    try:
        async with async_session() as session:
            await session.execute(
                update(User).where(User.id == user_id).values(is_blocked=1 if blocked else 0)
            )
            await session.commit()
        return True
    except Exception:
        return False


async def delete_product(product_id: int) -> bool:
    try:
        async with async_session() as session:
            await session.execute(delete(Product).where(Product.id == product_id))
            await session.commit()
        return True
    except Exception:
        return False


async def delete_shop(shop_id: int) -> bool:
    try:
        async with async_session() as session:
            await session.execute(delete(Shop).where(Shop.id == shop_id))
            await session.commit()
        return True
    except Exception:
        return False


# ============ MESSAGES ============
async def send_admin_message(
    user_id: int, subject: str, message: str, is_from_admin: bool = False
) -> bool:
    try:
        async with async_session() as session:
            msg = AdminMessage(
                user_id=user_id, subject=subject, message=message,
                is_from_admin=1 if is_from_admin else 0,
            )
            session.add(msg)
            await session.commit()
        return True
    except Exception:
        return False


async def get_user_messages(user_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(AdminMessage)
            .where(AdminMessage.user_id == user_id)
            .order_by(AdminMessage.created_at.desc())
        )
        rows = result.scalars().all()
        return [{c.name: getattr(r, c.name) for c in AdminMessage.__table__.columns} for r in rows]


async def get_all_messages() -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(AdminMessage, User.full_name, User.email)
            .join(User, AdminMessage.user_id == User.id)
            .order_by(AdminMessage.created_at.desc())
        )
        result = await session.execute(query)
        rows = []
        for r in result.all():
            d = {c.name: getattr(r.AdminMessage, c.name) for c in AdminMessage.__table__.columns}
            d["full_name"] = r.full_name
            d["email"] = r.email
            rows.append(d)
        return rows


async def reply_to_message(message_id: int, reply: str) -> bool:
    try:
        async with async_session() as session:
            await session.execute(
                update(AdminMessage)
                .where(AdminMessage.id == message_id)
                .values(admin_reply=reply, replied_at=_now(), is_read=0)
            )
            await session.commit()
        return True
    except Exception:
        return False


async def mark_message_read(message_id: int) -> bool:
    try:
        async with async_session() as session:
            await session.execute(
                update(AdminMessage).where(AdminMessage.id == message_id).values(is_read=1)
            )
            await session.commit()
        return True
    except Exception:
        return False


async def count_unread_messages() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(AdminMessage.id)).where(AdminMessage.is_read == 0)
        )
        return result.scalar() or 0


# ============ APP SETTINGS ============
async def get_app_settings() -> Dict[str, Any]:
    async with async_session() as session:
        result = await session.execute(select(AppSetting).where(AppSetting.id == 1))
        row = result.scalar_one_or_none()
        if row:
            return {"is_blocked": bool(row.is_blocked), "block_message": row.block_message}
        return {"is_blocked": False, "block_message": ""}


async def set_app_blocked(is_blocked: bool, block_message: str) -> bool:
    try:
        async with async_session() as session:
            await session.execute(
                update(AppSetting)
                .where(AppSetting.id == 1)
                .values(is_blocked=1 if is_blocked else 0, block_message=block_message)
            )
            await session.commit()
        return True
    except Exception:
        return False


# ============ VENDOR MESSAGES ============
async def send_vendor_message(shop_id: int, subject: str, message: str) -> bool:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Shop.owner_user_id).where(Shop.id == shop_id)
            )
            owner_id = result.scalar_one_or_none()
            if not owner_id:
                return False
            msg = VendorAdminMessage(
                shop_id=shop_id, vendor_user_id=owner_id,
                subject=subject, message=message, is_from_vendor=1,
            )
            session.add(msg)
            await session.commit()
        return True
    except Exception:
        return False


async def get_vendor_messages(shop_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        result = await session.execute(
            select(VendorAdminMessage)
            .where(VendorAdminMessage.shop_id == shop_id)
            .order_by(VendorAdminMessage.created_at.desc())
        )
        rows = result.scalars().all()
        return [{c.name: getattr(r, c.name) for c in VendorAdminMessage.__table__.columns} for r in rows]


async def reply_vendor_message(message_id: int, reply: str) -> bool:
    try:
        async with async_session() as session:
            await session.execute(
                update(VendorAdminMessage)
                .where(VendorAdminMessage.id == message_id)
                .values(admin_reply=reply, replied_at=_now(), is_read=0)
            )
            await session.commit()
        return True
    except Exception:
        return False


async def get_all_vendor_admin_messages() -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(VendorAdminMessage, Shop.shop_name)
            .join(Shop, VendorAdminMessage.shop_id == Shop.id)
            .order_by(VendorAdminMessage.created_at.desc())
        )
        result = await session.execute(query)
        rows = []
        for r in result.all():
            d = {c.name: getattr(r.VendorAdminMessage, c.name)
                 for c in VendorAdminMessage.__table__.columns}
            d["shop_name"] = r.shop_name
            rows.append(d)
        return rows


async def send_message_to_shop(shop_id: int, subject: str, message: str) -> bool:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Shop.owner_user_id).where(Shop.id == shop_id)
            )
            owner_id = result.scalar_one_or_none()
            if not owner_id:
                return False
            msg = VendorAdminMessage(
                shop_id=shop_id, vendor_user_id=owner_id,
                subject=subject, message=message, is_from_vendor=0,
            )
            session.add(msg)
            await session.commit()
        return True
    except Exception:
        return False


# ============ VENDOR STATS ============
async def count_shop_products(shop_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Product.id)).where(Product.shop_id == shop_id)
        )
        return result.scalar() or 0


async def count_shop_orders(shop_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Order.id))
            .join(Product, Order.product_id == Product.id)
            .where(Product.shop_id == shop_id)
        )
        return result.scalar() or 0


async def get_shop_revenue(shop_id: int) -> float:
    async with async_session() as session:
        result = await session.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0))
            .join(Product, Order.product_id == Product.id)
            .where(Product.shop_id == shop_id)
        )
        return float(result.scalar() or 0.0)


async def list_shop_orders(shop_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(
                Order, Product.name.label("product_name"),
                Product.image_url.label("product_image"),
                User.full_name.label("client_name"), User.email.label("client_email"),
            )
            .join(Product, Order.product_id == Product.id)
            .join(User, Order.client_user_id == User.id)
            .where(Product.shop_id == shop_id)
            .order_by(Order.id.desc())
        )
        result = await session.execute(query)
        rows = []
        for r in result.all():
            d = {c.name: getattr(r.Order, c.name) for c in Order.__table__.columns}
            d["product_name"] = r.product_name
            d["product_image"] = r.product_image
            d["client_name"] = r.client_name
            d["client_email"] = r.client_email
            rows.append(d)
        return rows


async def delete_product_by_owner(product_id: int, owner_user_id: int) -> Tuple[bool, str]:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Product).join(Shop).where(
                    Product.id == product_id,
                    Shop.owner_user_id == owner_user_id,
                )
            )
            product = result.scalar_one_or_none()
            if not product:
                return False, "Produit introuvable"
            await session.delete(product)
            await session.commit()
        return True, "Produit supprime"
    except Exception as e:
        return False, str(e)


async def update_order_status_if_shop(order_id: int, shop_id: int, status: str) -> bool:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Order).join(Product).where(
                    Order.id == order_id,
                    Product.shop_id == shop_id,
                )
            )
            order = result.scalar_one_or_none()
            if not order:
                return False
            order.status = status
            await session.commit()
        return True
    except Exception:
        return False


async def list_shop_orders_anonymous(shop_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(
                Order.id, Order.quantity, Order.total_amount, Order.status,
                Order.created_at, Product.name.label("product_name"),
                Product.image_url.label("product_image"),
                func.concat(
                    func.substr(User.full_name, 1, 1), "***",
                    func.substr(User.full_name, -1),
                ).label("client_name_masked"),
            )
            .join(Product, Order.product_id == Product.id)
            .join(User, Order.client_user_id == User.id)
            .where(Product.shop_id == shop_id)
            .order_by(Order.id.desc())
        )
        result = await session.execute(query)
        return [dict(r._mapping) for r in result.all()]


async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(Order, Product.name.label("product_name"))
            .join(Product, Order.product_id == Product.id)
            .where(Order.client_user_id == user_id)
            .order_by(Order.id.desc())
        )
        result = await session.execute(query)
        rows = []
        for r in result.all():
            d = {c.name: getattr(r.Order, c.name) for c in Order.__table__.columns}
            d["product_name"] = r.product_name
            rows.append(d)
        return rows


async def get_user_subscriptions(user_id: int) -> List[Dict[str, Any]]:
    async with async_session() as session:
        query = (
            select(Shop)
            .join(ShopSubscription, Shop.id == ShopSubscription.shop_id)
            .where(ShopSubscription.client_user_id == user_id)
            .order_by(ShopSubscription.subscribed_at.desc())
        )
        result = await session.execute(query)
        rows = result.scalars().all()
        return [{c.name: getattr(r, c.name) for c in Shop.__table__.columns} for r in rows]


async def seed_admin_and_demo():
    async with async_session() as session:
        admin = await session.execute(
            select(User).where(User.role == UserRole.admin).limit(1)
        )
        if admin.scalar_one_or_none():
            return

        salt, pwd_hash = _hash_password("admin123")
        session.add(User(
            full_name="Super Admin",
            email="admin@shop.local",
            password_hash=pwd_hash,
            password_salt=salt,
            role=UserRole.admin,
            is_verified=1,
        ))
        await session.flush()

        shops_data = [
            ("Boutique Tech", "tech@shop.local",
             "Boutique d'accessoires tech premium.", "contact@techshop.local",
             "",
             "",
             [("Ecouteurs Bluetooth", "Tech", 29.99, 20,
               "Son clair et autonomie elevee.",
               ""),
              ("Chargeur Rapide", "Tech", 14.50, 30, "Compatible USB-C.",
               "")]),
            ("Maison Mode", "mode@shop.local",
             "Mode chic et elegante pour tous les styles.", "contact@maisonmode.local",
             "",
             "",
             [("T-shirt Premium", "Mode", 18.00, 50, "Confortable et durable.",
               ""),
              ("Jean Slim", "Mode", 35.00, 25, "Style moderne.",
               "")]),
        ]

        for shop_name, email, desc, contact, logo_url, banner_url, products in shops_data:
            s, h = _hash_password("vendor123")
            vendor = User(
                full_name=shop_name, email=email, password_hash=h,
                password_salt=s, role=UserRole.boutique, is_verified=1,
            )
            session.add(vendor)
            await session.flush()
            shop = Shop(
                owner_user_id=vendor.id, shop_name=shop_name,
                description=desc, contact_info=contact,
                logo_url=logo_url, banner_url=banner_url,
            )
            session.add(shop)
            await session.flush()
            for p in products:
                session.add(Product(
                    shop_id=shop.id, name=p[0], category=p[1],
                    price=p[2], stock=p[3], description=p[4], image_url=p[5],
                ))
        await session.commit()


async def seed_default_settings():
    async with async_session() as session:
        await _ensure_default_settings(session)
        await session.commit()
