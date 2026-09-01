import { useCallback, useEffect, useState, type FormEvent } from 'react';
import * as api from '../lib/api';
import type { ProductRow, OrderRow, MessageRow, ShopRow, VendorStats } from '../lib/api';

interface Props {
  user: api.UserRow;
  shopId: number | null;
  shopName: string | null;
  onLogout: () => void;
}

type Tab = 'stats' | 'products' | 'orders' | 'shop' | 'messages';

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'stats', label: 'Dashboard', icon: '📊' },
  { id: 'products', label: 'Produits', icon: '🏷️' },
  { id: 'orders', label: 'Commandes', icon: '📦' },
  { id: 'shop', label: 'Ma boutique', icon: '🏪' },
  { id: 'messages', label: 'Messages', icon: '💬' },
];

export function VendorDashboard({ user, shopId: initialShopId, shopName, onLogout }: Props) {
  const [shopId] = useState<number | null>(initialShopId ?? null);
  const [activeTab, setActiveTab] = useState<Tab>(!shopId ? 'shop' : 'stats');

  if (!shopId) {
    return (
      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar-logo"><span>S</span> Spaceness</div>
          <nav className="sidebar-nav">
            <button className="sidebar-item active" onClick={() => setActiveTab('shop')}>
              <span>🏪</span> Ma boutique
            </button>
          </nav>
          <div className="sidebar-footer">
            <div className="sidebar-user">{user.full_name}</div>
            <div className="sidebar-user-sub">{user.email}</div>
            <button className="logout-btn" onClick={onLogout}>Déconnexion</button>
          </div>
        </aside>
        <main className="main-content">
          <div className="empty" style={{ paddingTop: 80 }}>
            <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Aucune boutique configurée</h2>
            <p style={{ color: 'var(--text-secondary)' }}>Contactez l'admin pour créer votre boutique.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo"><span>S</span> {shopName || 'Spaceness'}</div>
        <nav className="sidebar-nav">
          {TABS.map((t) => (
            <button key={t.id} className={`sidebar-item ${activeTab === t.id ? 'active' : ''}`} onClick={() => setActiveTab(t.id)}>
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">{user.full_name}</div>
          <div className="sidebar-user-sub">{user.email}</div>
          <button className="logout-btn" onClick={onLogout}>Déconnexion</button>
        </div>
      </aside>
      <main className="main-content">
        {activeTab === 'stats' && <StatsPage shopId={shopId} />}
        {activeTab === 'products' && <ProductsPage shopId={shopId} ownerUserId={user.id} />}
        {activeTab === 'orders' && <OrdersPage shopId={shopId} />}
        {activeTab === 'shop' && <ShopPage ownerUserId={user.id} />}
        {activeTab === 'messages' && <MessagesPage shopId={shopId} />}
      </main>
    </div>
  );
}

/* ===== Stats ===== */
function StatsPage({ shopId }: { shopId: number }) {
  const [stats, setStats] = useState<VendorStats | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.vendorStats(shopId);
    if (res.ok) setStats(res);
    setLoading(false);
  }, [shopId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Dashboard</h1><p className="page-subtitle">Statistiques de votre boutique</p></div></div>
      <div className="stats-grid">
        {[
          { label: 'Produits', value: stats?.total_products ?? 0, icon: '🏷️', color: 'blue' },
          { label: 'Commandes', value: stats?.total_orders ?? 0, icon: '📦', color: 'green' },
          { label: 'Revenu total', value: api.formatPrice(stats?.total_revenue ?? 0), icon: '💰', color: 'orange' },
          { label: 'Abonnés', value: stats?.total_subscribers ?? 0, icon: '👥', color: 'blue' },
          { label: 'En attente', value: stats?.pending_orders ?? 0, icon: '⏳', color: 'red' },
        ].map((s) => (
          <div key={s.label} className="stat-card">
            <div className={`icon ${s.color}`}>{s.icon}</div>
            <div className="value">{s.value}</div>
            <div className="label">{s.label}</div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ===== Products ===== */
function ProductsPage({ shopId, ownerUserId }: { shopId: number; ownerUserId: number }) {
  const [products, setProducts] = useState<ProductRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.vendorProducts(shopId);
    if (res.ok) setProducts(res.products);
    setLoading(false);
  }, [shopId]);

  useEffect(() => { load(); }, [load]);

  const remove = async (p: ProductRow) => {
    if (!confirm(`Supprimer "${p.name}" ?`)) return;
    const res = await api.vendorDeleteProduct(p.id, ownerUserId);
    if (res.ok) setProducts((prev) => prev.filter((x) => x.id !== p.id));
  };

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header">
        <div><h1 className="page-title">Mes produits</h1><p className="page-subtitle">{products.length} produits</p></div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Ajouter un produit</button>
      </div>
      <div className="card">
        <table><thead><tr><th>Nom</th><th>Catégorie</th><th>Prix</th><th>Stock</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead><tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td><strong>{p.name}</strong></td>
              <td><span className="badge badge-blue">{p.category}</span></td>
              <td>{api.formatPrice(p.price)}</td>
              <td>{p.stock > 0 ? <span className="badge badge-green">{p.stock}</span> : <span className="badge badge-red">Rupture</span>}</td>
              <td style={{ textAlign: 'right' }}><button className="btn btn-danger btn-sm" onClick={() => remove(p)}>Supprimer</button></td>
            </tr>
          ))}
          {products.length === 0 && <tr><td colSpan={5} className="empty">Aucun produit — ajoutez-en un !</td></tr>}
        </tbody></table>
      </div>
      {showAdd && <AddProductModal ownerUserId={ownerUserId} onClose={() => setShowAdd(false)} onAdded={() => { setShowAdd(false); load(); }} />}
    </>
  );
}

function AddProductModal({ ownerUserId, onClose, onAdded }: { ownerUserId: number; onClose: () => void; onAdded: () => void }) {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Autre');
  const [price, setPrice] = useState('');
  const [stock, setStock] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !price || !stock) { setError('Remplissez les champs obligatoires.'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await api.vendorAddProduct(ownerUserId, {
        name: name.trim(),
        category,
        price: parseFloat(price),
        stock: parseInt(stock, 10),
        description: description.trim() || undefined,
      });
      if (res.ok) onAdded();
      else setError(res.message || 'Erreur');
    } catch { setError('Erreur réseau.'); }
    finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2>Ajouter un produit</h2>
        <div className="form-row">
          <div className="form-group"><label className="form-label">Nom *</label><input className="form-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom du produit" /></div>
          <div className="form-group"><label className="form-label">Catégorie</label>
            <select className="form-input" value={category} onChange={(e) => setCategory(e.target.value)}>
              {['Tech', 'Mode', 'Maison', 'Alimentaire', 'Beauté', 'Sport', 'Autre'].map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div className="form-row">
          <div className="form-group"><label className="form-label">Prix (FC) *</label><input className="form-input" type="number" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="0" /></div>
          <div className="form-group"><label className="form-label">Stock *</label><input className="form-input" type="number" value={stock} onChange={(e) => setStock(e.target.value)} placeholder="0" /></div>
        </div>
        <div className="form-group"><label className="form-label">Description</label><textarea className="form-input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description du produit..." /></div>
        {error && <p className="error-msg">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Annuler</button>
          <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Ajout...' : 'Ajouter'}</button>
        </div>
      </form>
    </div>
  );
}

/* ===== Orders ===== */
function OrdersPage({ shopId }: { shopId: number }) {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.vendorOrders(shopId);
    if (res.ok) setOrders(res.orders);
    setLoading(false);
  }, [shopId]);

  useEffect(() => { load(); }, [load]);

  const updateStatus = async (orderId: number, status: string) => {
    const res = await api.vendorUpdateOrderStatus(orderId, shopId, status);
    if (res.ok) setOrders((prev) => prev.map((o) => o.id === orderId ? { ...o, status } : o));
  };

  const statusBadge = (s: string) => {
    const m: Record<string, string> = { pending: 'orange', shipped: 'blue', delivered: 'green', cancelled: 'red' };
    return <span className={`badge badge-${m[s] || 'gray'}`}>{s}</span>;
  };

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Commandes</h1><p className="page-subtitle">{orders.length} commandes pour votre boutique</p></div></div>
      <div className="card">
        <table><thead><tr><th>#</th><th>Produit</th><th>Qté</th><th>Montant</th><th>Statut</th><th>Date</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead><tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td>#{o.id}</td>
              <td>{o.product_name || `#${o.product_id}`}</td>
              <td>{o.quantity}</td>
              <td><strong>{api.formatPrice(o.total_amount)}</strong></td>
              <td>{statusBadge(o.status)}</td>
              <td>{api.formatDate(o.created_at)}</td>
              <td style={{ textAlign: 'right' }}>
                <select className="form-input" style={{ width: 130, padding: '5px 8px', fontSize: 13 }} value={o.status} onChange={(e) => updateStatus(o.id, e.target.value)}>
                  {['pending', 'shipped', 'delivered', 'cancelled'].map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
            </tr>
          ))}
          {orders.length === 0 && <tr><td colSpan={7} className="empty">Aucune commande</td></tr>}
        </tbody></table>
      </div>
    </>
  );
}

/* ===== Shop Info ===== */
function ShopPage({ ownerUserId }: { ownerUserId: number }) {
  const [shop, setShop] = useState<ShopRow | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.vendorShop(ownerUserId);
    if (res.ok) setShop(res.shop);
    setLoading(false);
  }, [ownerUserId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="loader">Chargement...</div>;
  if (!shop) return <div className="empty">Boutique introuvable.</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Ma boutique</h1><p className="page-subtitle">{shop.shop_name}</p></div></div>
      <div className="card" style={{ maxWidth: 600 }}>
        <div className="card-header"><span className="card-title">Informations de la boutique</span></div>
        <div style={{ padding: 20 }}>
          <div className="form-group"><label className="form-label">Nom</label><div style={{ fontSize: 15, fontWeight: 600 }}>{shop.shop_name}</div></div>
          <div className="form-group"><label className="form-label">Description</label><div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{shop.description || 'Aucune description'}</div></div>
          <div className="form-group"><label className="form-label">Contact</label><div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{shop.contact_info || '—'}</div></div>
        </div>
      </div>
    </>
  );
}

/* ===== Messages ===== */
function MessagesPage({ shopId }: { shopId: number }) {
  const [messages, setMessages] = useState<MessageRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.vendorMessages(shopId);
    if (res.ok) setMessages(res.messages);
    setLoading(false);
  }, [shopId]);

  useEffect(() => { load(); }, [load]);

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !message.trim()) return;
    setSending(true);
    await fetch(`${api.API_URL}/api/vendor/messages?shop_id=${shopId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject: subject.trim(), message: message.trim() }),
    });
    setSubject('');
    setMessage('');
    setSending(false);
    load();
  };

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Messages</h1><p className="page-subtitle">Communication avec l'administration</p></div></div>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header"><span className="card-title">Nouveau message</span></div>
        <form style={{ padding: 20 }} onSubmit={handleSend}>
          <div className="form-group"><input className="form-input" value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Sujet..." /></div>
          <div className="form-group"><textarea className="form-input" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Votre message..." rows={3} /></div>
          <button className="btn btn-primary" type="submit" disabled={sending || !subject.trim() || !message.trim()}>
            {sending ? 'Envoi...' : 'Envoyer'}
          </button>
        </form>
      </div>
      <div className="card">
        <table><thead><tr><th>Date</th><th>Sujet</th><th>Message</th><th>Réponse</th></tr></thead><tbody>
          {messages.map((m) => (
            <tr key={m.id}>
              <td>{api.formatDate(m.created_at)}</td>
              <td><strong>{m.subject}</strong></td>
              <td>{m.message}</td>
              <td style={{ color: m.admin_reply ? 'var(--success)' : 'var(--text-light)' }}>{m.admin_reply || '—'}</td>
            </tr>
          ))}
          {messages.length === 0 && <tr><td colSpan={4} className="empty">Aucun message</td></tr>}
        </tbody></table>
      </div>
    </>
  );
}