// Client API Spaceness — miroir TypeScript de api_client.py
// Le backend FastAPI reste inchangé, toutes les routes sont identiques.

import { Platform } from 'react-native';
import type {
  AppSettings,
  Message,
  Order,
  Product,
  Review,
  Shop,
  User,
  VersionInfo,
} from './types';

// URL du backend. À ajuster selon l'environnement.
// En production : https://spaceness.onrender.com
const DEFAULT_API_URL = 'https://spaceness.onrender.com';

export const API_URL = DEFAULT_API_URL;

function buildUrl(path: string, params?: Record<string, string | number | undefined>) {
  const url = `${API_URL}${path}`;
  if (!params) return url;
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
  return qs ? `${url}?${qs}` : url;
}

async function request<T>(method: string, path: string, data?: unknown, params?: Record<string, string | number | undefined>, timeout = 30000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const res = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: data !== undefined ? JSON.stringify(data) : undefined,
      signal: controller.signal,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok && !json.ok) {
      throw new ApiError(res.status, json.detail || json.message || `Erreur ${res.status}`);
    }
    return json as T;
  } finally {
    clearTimeout(timer);
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// ============ AUTH ============
export interface LoginResponse { ok: boolean; message?: string; user?: User; verification_required?: boolean }

export async function login(email: string, password: string): Promise<LoginResponse> {
  try {
    return await request<LoginResponse>('POST', '/api/auth/login', { email, password });
  } catch (e) {
    return { ok: false, message: (e as Error).message || 'Erreur de connexion' };
  }
}

export async function register(fullName: string, email: string, password: string, role = 'client') {
  return request<{ ok: boolean; message?: string }>('POST', '/api/auth/register', { full_name: fullName, email, password, role });
}

export async function getUserById(userId: number): Promise<User | null> {
  try {
    const res = await request<{ ok: boolean; user: User }>('POST', '/api/auth/get-user', { user_id: userId });
    return res.ok ? res.user : null;
  } catch {
    return null;
  }
}

export async function verifyEmailCode(userId: number, code: string) {
  try {
    const res = await request<{ ok: boolean; message?: string; user?: User }>('POST', '/api/auth/verify-code', { user_id: userId, code });
    return { ok: res.ok, message: res.message || (res.ok ? 'Email vérifié !' : 'Code incorrect.'), user: res.user };
  } catch (e) {
    return { ok: false, message: (e as Error).message, user: undefined };
  }
}

export async function resendVerificationCode(userId: number): Promise<string | null> {
  try {
    const res = await request<{ ok: boolean; code?: string }>('POST', '/api/auth/resend-code', { user_id: userId });
    return res.ok && res.code ? res.code : null;
  } catch {
    return null;
  }
}

export async function forgotPassword(email: string) {
  try {
    const res = await request<{ ok: boolean; code?: string }>('POST', '/api/auth/forgot-password', { email });
    return { ok: res.ok, code: res.code };
  } catch (e) {
    return { ok: false, code: undefined, message: (e as Error).message };
  }
}

export async function resetPassword(email: string, code: string, newPassword: string) {
  try {
    const res = await request<{ ok: boolean; message?: string }>('POST', '/api/auth/reset-password', { email, code, new_password: newPassword });
    return { ok: res.ok, message: res.message };
  } catch (e) {
    return { ok: false, message: (e as Error).message };
  }
}

// ============ PRODUITS ============
export async function listProducts(search = '', category = ''): Promise<Product[]> {
  try {
    const res = await request<{ ok: boolean; products: Product[] }>('GET', '/api/products', undefined, { search, category });
    return res.products || [];
  } catch {
    return [];
  }
}

export async function getProductById(productId: number): Promise<Product | null> {
  try {
    const res = await request<{ ok: boolean; product: Product }>('GET', `/api/products/${productId}`);
    return res.ok ? res.product : null;
  } catch {
    return null;
  }
}

export async function listShopProducts(shopId: number): Promise<Product[]> {
  try {
    const res = await request<{ ok: boolean; products: Product[] }>('GET', `/api/shops/${shopId}/products`);
    return res.products || [];
  } catch {
    return [];
  }
}

// ============ BOUTIQUES ============
export async function getShopDetails(shopId: number): Promise<Shop | null> {
  try {
    const res = await request<{ ok: boolean; shop: Shop }>('GET', `/api/shops/${shopId}`);
    return res.ok ? res.shop : null;
  } catch {
    return null;
  }
}

// ============ COMMANDES ============
export async function createOrdersFromCart(userId: number, items: { product_id: number; qty: number }[], deliveryAddress = '', deliveryPhone = '') {
  try {
    return await request<{ ok: boolean; message?: string; order_ids?: number[] }>('POST', '/api/orders/from-cart', {
      user_id: userId, items, delivery_address: deliveryAddress, delivery_phone: deliveryPhone,
    });
  } catch (e) {
    return { ok: false, message: (e as Error).message };
  }
}

export async function listOrdersForClient(clientUserId: number): Promise<Order[]> {
  try {
    const res = await request<{ ok: boolean; orders: Order[] }>('GET', `/api/orders/client/${clientUserId}`);
    return res.orders || [];
  } catch {
    return [];
  }
}

export function orderQrUrl(orderId: number): string {
  return `${API_URL}/api/orders/qr/${orderId}`;
}

// ============ FAVORIS ============
export async function addToFavorites(userId: number, productId: number): Promise<boolean> {
  try {
    const res = await request<{ ok: boolean }>('POST', '/api/favorites/add', { user_id: userId, product_id: productId });
    return !!res.ok;
  } catch { return false; }
}
export async function removeFromFavorites(userId: number, productId: number): Promise<boolean> {
  try {
    const res = await request<{ ok: boolean }>('POST', '/api/favorites/remove', { user_id: userId, product_id: productId });
    return !!res.ok;
  } catch { return false; }
}
export async function isFavorite(userId: number, productId: number): Promise<boolean> {
  try {
    const res = await request<{ ok: boolean; is_favorite?: boolean }>('POST', '/api/favorites/check', { user_id: userId, product_id: productId });
    return !!res.is_favorite;
  } catch { return false; }
}
export async function listFavorites(userId: number): Promise<Product[]> {
  try {
    const res = await request<{ ok: boolean; favorites: Product[] }>('GET', `/api/favorites/${userId}`);
    return res.favorites || [];
  } catch { return []; }
}

// ============ HISTORIQUE ============
export async function addToHistory(userId: number, productId: number): Promise<void> {
  try { await request('POST', '/api/history/add', { user_id: userId, product_id: productId }); } catch {}
}
export async function listHistory(userId: number): Promise<Product[]> {
  try {
    const res = await request<{ ok: boolean; history: Product[] }>('GET', `/api/history/${userId}`);
    return res.history || [];
  } catch { return []; }
}
export async function clearHistory(userId: number): Promise<void> {
  try { await request('POST', '/api/history/clear', { user_id: userId }); } catch {}
}

// ============ AVIS ============
export async function addReview(userId: number, productId: number, rating: number, comment = ''): Promise<boolean> {
  try {
    const res = await request<{ ok: boolean }>('POST', '/api/reviews/add', { user_id: userId, product_id: productId, rating, comment });
    return !!res.ok;
  } catch { return false; }
}
export async function getProductReviews(productId: number): Promise<{ reviews: Review[]; rating: number; count: number }> {
  try {
    const res = await request<{ ok: boolean; reviews: Review[]; rating: number; count: number }>('GET', `/api/reviews/${productId}`);
    return { reviews: res.reviews || [], rating: res.rating || 0, count: res.count || 0 };
  } catch { return { reviews: [], rating: 0, count: 0 }; }
}

// ============ ABONNEMENTS ============
export async function subscribeToShop(clientUserId: number, shopId: number): Promise<boolean> {
  try { const r = await request<{ ok: boolean }>('POST', '/api/subscriptions/subscribe', { client_user_id: clientUserId, shop_id: shopId }); return !!r.ok; } catch { return false; }
}
export async function unsubscribeFromShop(clientUserId: number, shopId: number): Promise<boolean> {
  try { const r = await request<{ ok: boolean }>('POST', '/api/subscriptions/unsubscribe', { client_user_id: clientUserId, shop_id: shopId }); return !!r.ok; } catch { return false; }
}
export async function isSubscribedToShop(clientUserId: number, shopId: number): Promise<boolean> {
  try {
    const res = await request<{ ok: boolean; shops: Shop[] }>('GET', `/api/subscriptions/${clientUserId}`);
    return (res.shops || []).some((s) => s.id === shopId);
  } catch { return false; }
}
export async function listSubscribedShops(clientUserId: number): Promise<Shop[]> {
  try { const r = await request<{ ok: boolean; shops: Shop[] }>('GET', `/api/subscriptions/${clientUserId}`); return r.shops || []; } catch { return []; }
}

// ============ MESSAGES ============
export async function sendAdminMessage(userId: number, subject: string, message: string): Promise<boolean> {
  try { const r = await request<{ ok: boolean }>('POST', '/api/messages/send', { user_id: userId, subject, message }); return !!r.ok; } catch { return false; }
}
export async function getUserMessages(userId: number): Promise<Message[]> {
  try { const r = await request<{ ok: boolean; messages: Message[] }>('GET', `/api/messages/${userId}`, undefined, undefined, 20000); return r.messages || []; } catch { return []; }
}
export async function markMessageRead(messageId: number): Promise<void> {
  try { await request('POST', '/api/admin/messages/read', { message_id: messageId }); } catch {}
}

// ============ PARAMÈTRES APP ============
export async function getAppSettings(): Promise<AppSettings> {
  try { const r = await request<{ ok: boolean; settings: AppSettings }>('GET', '/api/app-settings'); return r.settings || { is_blocked: false }; } catch { return { is_blocked: false }; }
}

// ============ VERSION ============
export async function checkVersion(): Promise<VersionInfo> {
  try { const r = await request<{ ok: boolean } & VersionInfo>('GET', '/api/app-version'); return r; } catch { return {}; }
}

// ============ UPLOAD ============
export async function uploadImage(uri: string): Promise<string | null> {
  try {
    const form = new FormData();
    const name = uri.split('/').pop() || 'photo.jpg';
    form.append('file', { uri, name, type: 'image/jpeg' } as unknown as Blob);
    const res = await fetch(`${API_URL}/api/upload`, { method: 'POST', body: form });
    const json = await res.json();
    return json.ok ? json.url : null;
  } catch { return null; }
}

// ============ HELPER ============
export function safeImage(url?: string, fallback?: string): string | undefined {
  if (!url) return fallback;
  if (url.startsWith('/uploads/')) return `${API_URL}${url}`;
  return url;
}
