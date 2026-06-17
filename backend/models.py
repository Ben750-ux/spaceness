import enum
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    CheckConstraint, Column, DateTime, Enum, Float, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from config import settings


engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    client = "client"
    boutique = "boutique"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.client)
    is_blocked = Column(Integer, nullable=False, default=0)
    is_verified = Column(Integer, nullable=False, default=0)
    verification_code = Column(String(255), nullable=True)
    verification_code_expires = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    shop = relationship("Shop", back_populates="owner", uselist=False, cascade="all, delete-orphan")


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    shop_name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False, default="")
    contact_info = Column(Text, nullable=False, default="")
    logo_url = Column(Text, nullable=False, default="")
    banner_url = Column(Text, nullable=False, default="")

    owner = relationship("User", back_populates="shop")
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    subscriptions = relationship("ShopSubscription", back_populates="shop", cascade="all, delete-orphan")
    vendor_messages = relationship("VendorAdminMessage", back_populates="shop", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="General")
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=False, default="")
    image_url = Column(Text, nullable=False, default="")
    image_url_2 = Column(Text, nullable=False, default="")
    image_url_3 = Column(Text, nullable=False, default="")
    is_active = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price"),
        CheckConstraint("stock >= 0", name="check_stock"),
        Index("idx_products_shop_id", "shop_id"),
    )

    shop = relationship("Shop", back_populates="products")
    orders = relationship("Order", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="product", cascade="all, delete-orphan")
    view_history = relationship("ViewHistory", back_populates="product", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity"),
        CheckConstraint("total_amount >= 0", name="check_total_amount"),
        Index("idx_orders_client", "client_user_id"),
    )

    product = relationship("Product", back_populates="orders")


class ShopSubscription(Base):
    __tablename__ = "shop_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    subscribed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_subscriptions_client", "client_user_id"),
        Index("idx_subscriptions_shop", "shop_id"),
        UniqueConstraint("client_user_id", "shop_id", name="uq_sub_client_shop"),
    )

    shop = relationship("Shop", back_populates="subscriptions")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_favorites_user", "user_id"),
        UniqueConstraint("user_id", "product_id", name="uq_fav_user_product"),
    )

    product = relationship("Product", back_populates="favorites")


class ViewHistory(Base):
    __tablename__ = "view_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_history_user", "user_id"),
    )

    product = relationship("Product", back_populates="view_history")


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating"),
        Index("idx_reviews_product", "product_id"),
        UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
    )

    product = relationship("Product", back_populates="reviews")


class AdminMessage(Base):
    __tablename__ = "admin_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    admin_reply = Column(Text, nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_read = Column(Integer, nullable=False, default=0)
    is_from_admin = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_messages_user", "user_id"),
    )


class VendorAdminMessage(Base):
    __tablename__ = "vendor_admin_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    vendor_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    admin_reply = Column(Text, nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_read = Column(Integer, nullable=False, default=0)
    is_from_vendor = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("idx_vendor_messages_shop", "shop_id"),
    )

    shop = relationship("Shop", back_populates="vendor_messages")


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    is_blocked = Column(Integer, nullable=False, default=0)
    block_message = Column(Text, nullable=False, default="")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    ip_address = Column(String(255), nullable=True)
    attempted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    success = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_login_attempts_email", "email"),
    )


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    user_name = Column(String(255), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_activity_log_user", "user_id"),
    )


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
