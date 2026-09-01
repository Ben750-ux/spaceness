import { useState, type FormEvent } from 'react';
import { adminLogin, vendorLogin } from '../lib/api';
import type { UserRow } from '../lib/api';

interface Props {
  onLogin: (auth: { role: 'admin' | 'vendor'; user: UserRow; shopId?: number | null; shopName?: string | null }) => void;
}

export function Login({ onLogin }: Props) {
  const [role, setRole] = useState<'admin' | 'vendor'>('admin');
  const [email, setEmail] = useState(role === 'admin' ? 'admin@shop.local' : 'tech@shop.local');
  const [password, setPassword] = useState(role === 'admin' ? 'admin123' : 'vendor123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const switchRole = (r: 'admin' | 'vendor') => {
    setRole(r);
    setEmail(r === 'admin' ? 'admin@shop.local' : 'tech@shop.local');
    setPassword(r === 'admin' ? 'admin123' : 'vendor123');
    setError('');
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Remplissez tous les champs.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      if (role === 'admin') {
        const res = await adminLogin(email.trim(), password);
        if (res.ok && res.user && res.user.role === 'admin') {
          onLogin({ role: 'admin', user: res.user });
        } else {
          setError(res.message || 'Identifiants incorrects.');
        }
      } else {
        const res = await vendorLogin(email.trim(), password);
        if (res.ok && res.vendor) {
          onLogin({
            role: 'vendor',
            user: { id: res.vendor.id, full_name: res.vendor.full_name, email: res.vendor.email, role: 'boutique', is_verified: 1 },
            shopId: res.vendor.shop_id,
            shopName: res.vendor.shop_name,
          });
        } else {
          setError('Identifiants incorrects.');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion au serveur.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <h1>Spaceness</h1>
        <p className="subtitle">Gestion de la plateforme</p>

        <div className="role-tabs">
          <button type="button" className={`role-tab ${role === 'admin' ? 'active' : ''}`} onClick={() => switchRole('admin')}>Admin</button>
          <button type="button" className={`role-tab ${role === 'vendor' ? 'active' : ''}`} onClick={() => switchRole('vendor')}>Boutique</button>
        </div>

        <div className="form-group">
          <label className="form-label">Email</label>
          <input className="form-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoCapitalize="none" />
        </div>
        <div className="form-group">
          <label className="form-label">Mot de passe</label>
          <input className="form-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>

        {error && <p className="error-msg">{error}</p>}

        <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%', padding: '12px', fontSize: '15px' }}>
          {loading ? 'Connexion...' : 'Se connecter'}
        </button>
      </form>
    </div>
  );
}