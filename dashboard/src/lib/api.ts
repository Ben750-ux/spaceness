export const API_URL =
  import.meta.env.VITE_API_URL || 'https://spaceness.onrender.com';

export type Role = 'client' | 'boutique' | 'admin';

export interface UserRow {
  id: number;
  full_name: string;
  email: string;
  phone?: string | null;
  address?: string | null;
  role: Role;
  is_verified: 0 | 1;
  is_blocked?: 0 | 1;
  created_at?: string;
}

export interface ShopRow {
  id: number;
  shop_name: string;
  description?: string | null;
  contact_info?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  owner_user_id?: number | null;
  owner_name?: string | null;
  owner_email?: string | null;
  created_at?: string;
}

export interface ProductRow {
  id: number;
  shop_id: number;
  shop_name?: string;
  name: string;
  category: string;
  price: number;
  stock: number;
  description?: string;
  image_url?: string;
  is_active?: number;
  created_at?: string;
}

export interface OrderRow {
  id: number;
  client_user_id?: number;
  client_name?: string;
  shop_id?: number;
  shop_name?: string;
  product_id: number;
  product_name?: string;
  quantity: number;
  total_amount: number;
  status: string;
  created_at?: string;
  delivery_address?: string;
  delivery_phone?: string;
}

export interface MessageRow {
  id: number;
  user_id?: number;
  full_name?: string;
  email?: string;
  shop_id?: number;
  shop_name?: string;
  subject: string;
  message: string;
  admin_reply?: string | null;
  created_at?: string;
  replied_at?: string;
  is_from_admin?: number;
  is_from_vendor?: number;
}

export interface AdminConversation {
  user_id?: number;
  full_name?: string;
  email?: string;
  shop_id?: number;
  shop_name?: string;
  last_message?: string;
  created_at?: string;
}

export interface ActivityLog {
  id?: number;
  action: string;
  description?: string;
  timestamp?: string;
  user_name?: string;
}

export interface AdminStats {
  users: number;
  products: number;
  orders: number;
  shops: number;
}

export interface VendorStats {
  total_products: number;
  total_orders: number;
  total_revenue: number;
  total_subscribers: number;
  pending_orders: number;
}

export interface MonthlyStat {
  month?: string;
  label?: string;
  total?: number;
  revenue?: number;
}

export interface PopularProduct {
  id?: number;
  name?: string;
  total?: number;
}

interface ApiError {
  detail?: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    let msg = `Erreur ${res.status}`;
    try {
      const body = (await res.json()) as ApiError;
      if (body.detail) msg = body.detail;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) });
}

function put<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: 'PUT', body: JSON.stringify(body ?? {}) });
}

function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

// ---------- AUTH ----------
export const adminLogin = (email: string, password: string) =>
  post<{ ok: boolean; user?: UserRow; message?: string }>('/api/auth/login', { email, password });

export const vendorLogin = (email: string, password: string) =>
  post<{ ok: boolean; vendor?: { id: number; full_name: string; email: string; role: string; shop_id: number | null; shop_name: string | null } }>(
    '/api/vendor/login',
    { email, password },
  );

// ---------- ADMIN : stats ----------
export const adminStats = () => request<{ ok: boolean } & AdminStats>('/api/admin/stats');
export const adminAdvancedStats = (days = 30) =>
  request<{ ok: boolean; daily_orders: unknown[]; popular_products: PopularProduct[]; monthly_stats: MonthlyStat[] }>(
    `/api/admin/stats/advanced?days=${days}`,
  );

// ---------- ADMIN : entités ----------
export const adminUsers = () => request<{ ok: boolean; users: UserRow[] }>('/api/admin/users');
export const adminBlockUser = (userId: number, blocked: boolean) =>
  post<{ ok: boolean; message?: string }>('/api/admin/users/block', { user_id: userId, blocked });
export const adminDeleteUser = (userId: number) =>
  post<{ ok: boolean }>('/api/admin/users/delete', { user_id: userId });

export const adminOrders = () => request<{ ok: boolean; orders: OrderRow[] }>('/api/admin/orders');
export const adminUpdateOrderStatus = (orderId: number, status: string) =>
  put<{ ok: boolean }>(`/api/admin/orders/${orderId}/status`, { status });

export const adminProducts = () => request<{ ok: boolean; products: ProductRow[] }>('/api/admin/products');
export const adminDeleteProduct = (productId: number) => del<{ ok: boolean }>(`/api/admin/products/${productId}`);

export const adminShops = () => request<{ ok: boolean; shops: ShopRow[] }>('/api/admin/shops');
export const adminDeleteShop = (shopId: number) => del<{ ok: boolean }>(`/api/admin/shops/${shopId}`);

// ---------- ADMIN : messages ----------
export const adminMessages = () => request<{ ok: boolean; messages: MessageRow[] }>('/api/admin/messages');
export const adminReplyMessage = (messageId: number, reply: string) =>
  post<{ ok: boolean }>('/api/admin/messages/reply', { message_id: messageId, reply });

export const adminVendorMessages = () =>
  request<{ ok: boolean; messages: MessageRow[] }>('/api/admin/vendor-messages');
export const adminReplyVendorMessage = (messageId: number, reply: string) =>
  post<{ ok: boolean }>(`/api/admin/vendor-messages/${messageId}/reply`, { reply });

export const adminClientConversations = () =>
  request<{ ok: boolean; conversations: AdminConversation[] }>('/api/admin/conversations/clients');
export const adminClientConversation = (userId: number) =>
  request<{ ok: boolean; messages: MessageRow[] }>(`/api/admin/conversations/clients/${userId}`);

export const adminShopConversations = () =>
  request<{ ok: boolean; conversations: AdminConversation[] }>('/api/admin/conversations/shops');
export const adminShopConversation = (shopId: number) =>
  request<{ ok: boolean; messages: MessageRow[] }>(`/api/admin/conversations/shops/${shopId}`);

export const adminActivityLog = (limit = 100) =>
  request<{ ok: boolean; logs: ActivityLog[] }>(`/api/admin/activity-log?limit=${limit}`);

// ---------- VENDOR ----------
export const vendorShop = (ownerUserId: number) =>
  request<{ ok: boolean; shop: ShopRow }>(`/api/vendor/shop?owner_user_id=${ownerUserId}`);
export const vendorStats = (shopId: number) =>
  request<{ ok: boolean } & VendorStats>(`/api/vendor/stats?shop_id=${shopId}`);
export const vendorMonthlyStats = (shopId: number) =>
  request<{ ok: boolean; stats: MonthlyStat[] }>(`/api/vendor/stats/monthly?shop_id=${shopId}`);
export const vendorProducts = (shopId: number) =>
  request<{ ok: boolean; products: ProductRow[] }>(`/api/vendor/products?shop_id=${shopId}`);
export const vendorAddProduct = (
  ownerUserId: number,
  data: { name: string; category: string; price: number; stock: number; description?: string; image_url?: string },
) =>
  post<{ ok: boolean; message?: string }>('/api/vendor/products', {
    owner_user_id: ownerUserId,
    ...data,
  });
export const vendorUpdateProduct = (productId: number, ownerUserId: number, stock: number, isActive: number) =>
  put<{ ok: boolean; message?: string }>(`/api/vendor/products/${productId}?owner_user_id=${ownerUserId}`, {
    stock, is_active: isActive,
  });
export const vendorDeleteProduct = (productId: number, ownerUserId: number) =>
  del<{ ok: boolean; message?: string }>(`/api/vendor/products/${productId}?owner_user_id=${ownerUserId}`);
export const vendorOrders = (shopId: number) =>
  request<{ ok: boolean; orders: OrderRow[] }>(`/api/vendor/orders?shop_id=${shopId}`);
export const vendorUpdateOrderStatus = (orderId: number, shopId: number, status: string) =>
  put<{ ok: boolean }>(`/api/vendor/orders/${orderId}/status?shop_id=${shopId}`, { status });
export const vendorMessages = (shopId: number) =>
  request<{ ok: boolean; messages: MessageRow[] }>(`/api/vendor/messages?shop_id=${shopId}`);

// ---------- utilitaires ----------
export function formatPrice(n: number): string {
  return n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' FC';
}

export function formatDate(s?: string): string {
  if (!s) return '—';
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}