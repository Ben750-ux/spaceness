import { useState, useEffect } from 'react';
import { Login } from './pages/Login';
import { AdminDashboard } from './pages/AdminDashboard';
import { VendorDashboard } from './pages/VendorDashboard';
import type { UserRow } from './lib/api';

interface AuthState {
  role: 'admin' | 'vendor';
  user: UserRow;
  shopId?: number | null;
  shopName?: string | null;
}

const STORAGE_KEY = 'spaceness_dash_auth';

function loadAuth(): AuthState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [auth, setAuth] = useState<AuthState | null>(loadAuth);

  useEffect(() => {
    if (auth) localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
    else localStorage.removeItem(STORAGE_KEY);
  }, [auth]);

  const logout = () => setAuth(null);

  if (!auth) return <Login onLogin={setAuth} />;
  if (auth.role === 'admin')
    return <AdminDashboard user={auth.user} onLogout={logout} />;
  return     <VendorDashboard user={auth.user} shopId={auth.shopId ?? null} shopName={auth.shopName ?? null} onLogout={logout} />;
}