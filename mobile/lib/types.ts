// Types partagés de l'application (miroir des modèles du backend FastAPI)

export interface User {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  address?: string;
  role: string; // client | vendeur | admin
  is_verified?: boolean | number;
  is_blocked?: boolean | number;
  birth_date?: string;
  gender?: string;
  created_at?: string;
}

export interface Product {
  id: number;
  shop_id: number;
  shop_name?: string;
  name: string;
  category: string;
  price: number;
  stock: number;
  description?: string;
  image_url?: string;
  image_url_2?: string;
  image_url_3?: string;
  is_active?: number | boolean;
  rating?: number;
  review_count?: number;
}

export interface Shop {
  id: number;
  owner_user_id?: number;
  shop_name: string;
  description?: string;
  contact_info?: string;
  logo_url?: string;
  banner_url?: string;
  is_active?: number | boolean;
}

export interface Order {
  id: number;
  client_user_id?: number;
  shop_id?: number;
  shop_name?: string;
  product_id?: number;
  product_name?: string;
  product_image_url?: string;
  quantity: number;
  total_amount: number;
  status: string; // pending | confirmed | shipped | delivered | cancelled
  delivery_address?: string;
  delivery_phone?: string;
  delivery_code?: string;
  created_at: string;
}

export interface Review {
  id: number;
  user_id?: number;
  user_name?: string;
  product_id?: number;
  rating: number;
  comment?: string;
  created_at?: string;
}

export interface Message {
  id: number;
  user_id?: number;
  subject: string;
  message: string;
  admin_reply?: string;
  is_read?: boolean | number;
  created_at?: string;
}

export interface CartItem {
  product_id: number;
  name: string;
  price: number;
  qty: number;
  image_url?: string;
  shop_name?: string;
  shop_id?: number;
  stock?: number;
}

export interface AppSettings {
  is_blocked: boolean | number;
  block_message?: string;
}

export interface VersionInfo {
  latest_version?: string;
  min_version?: string;
  download_url?: string;
  update_message?: string;
}
