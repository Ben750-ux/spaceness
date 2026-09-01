// Contexte global de l'app : authentification, session et panier.
// Remplace la classe ShopMobileApp de main.py.

import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as api from '@/lib/api';
import type { CartItem, User } from '@/lib/types';

const SESSION_KEY = 'spaceness_session';

interface AuthState {
  user: User | null;
  loading: boolean;
  cart: CartItem[];
  cartCount: number;
}

interface AuthContextValue extends AuthState {
  signIn: (user: User) => Promise<void>;
  signOut: () => Promise<void>;
  restoreSession: () => Promise<boolean>;
  updateUser: (user: User) => void;
  addToCart: (item: Omit<CartItem, 'qty'> & { qty?: number }) => { ok: boolean; message: string };
  setCartQty: (productId: number, qty: number) => void;
  removeFromCart: (productId: number) => void;
  clearCart: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState<CartItem[]>([]);

  const cartCount = useMemo(() => cart.reduce((sum, i) => sum + (i.qty || 0), 0), [cart]);

  const persistUser = useCallback(async (u: User | null) => {
    try {
      if (u) {
        await AsyncStorage.setItem(SESSION_KEY, JSON.stringify(u));
      } else {
        await AsyncStorage.removeItem(SESSION_KEY);
      }
    } catch {}
  }, []);

  const signIn = useCallback(async (u: User) => {
    setUser(u);
    await persistUser(u);
  }, [persistUser]);

  const signOut = useCallback(async () => {
    setUser(null);
    setCart([]);
    await persistUser(null);
  }, [persistUser]);

  const restoreSession = useCallback(async (): Promise<boolean> => {
    try {
      const raw = await AsyncStorage.getItem(SESSION_KEY);
      if (!raw) return false;
      const saved: User = JSON.parse(raw);
      if (!saved || !saved.id) return false;
      // Revalide la session auprès du serveur
      const fresh = await api.getUserById(saved.id);
      if (fresh && fresh.role === 'client' && (fresh.is_verified === 1 || fresh.is_verified === true || fresh.is_verified === undefined)) {
        const valid = { ...fresh, is_verified: true };
        setUser(valid);
        await persistUser(valid);
      } else {
        await persistUser(null);
        return false;
      }
    } catch {
      return false;
    } finally {
      setLoading(false);
    }
    return true;
  }, [persistUser]);

  const updateUser = useCallback((u: User) => {
    setUser(u);
    persistUser(u);
  }, [persistUser]);

  const addToCart = useCallback((item: Omit<CartItem, 'qty'> & { qty?: number }) => {
    const qty = item.qty || 1;
    if (qty <= 0) return { ok: false, message: 'Quantité invalide.' };

    let result: { ok: boolean; message: string } = { ok: true, message: 'Ajouté au panier.' };

    setCart((prev) => {
      const existing = prev.find((i) => i.product_id === item.product_id);
      const stock = item.stock;
      if (existing) {
        const newQty = existing.qty + qty;
        if (stock !== undefined && newQty > stock) {
          result = { ok: false, message: 'Stock insuffisant pour cette quantité.' };
          return prev;
        }
        return prev.map((i) => (i.product_id === item.product_id ? { ...i, qty: newQty } : i));
      }
      if (stock !== undefined && qty > stock) {
        result = { ok: false, message: 'Stock insuffisant.' };
        return prev;
      }
      return [...prev, { product_id: item.product_id, name: item.name, price: item.price, qty, image_url: item.image_url, shop_name: item.shop_name, shop_id: item.shop_id, stock: item.stock }];
    });
    return result;
  }, []);

  const removeFromCart = useCallback((productId: number) => {
    setCart((prev) => prev.filter((i) => i.product_id !== productId));
  }, []);

  const setCartQty = useCallback((productId: number, qty: number) => {
    setCart((prev) => prev.map((i) => (i.product_id === productId ? { ...i, qty: Math.max(1, qty) } : i)));
  }, []);

  const clearCart = useCallback(() => setCart([]), []);

  useEffect(() => {
    restoreSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo(
    () => ({ user, loading, cart, cartCount, signIn, signOut, restoreSession, updateUser, addToCart, setCartQty, removeFromCart, clearCart }),
    [user, loading, cart, cartCount, signIn, signOut, restoreSession, updateUser, addToCart, setCartQty, removeFromCart, clearCart],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
