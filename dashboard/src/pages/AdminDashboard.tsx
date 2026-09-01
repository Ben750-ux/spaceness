import { useCallback, useEffect, useState } from 'react';
import * as api from '../lib/api';
import type { UserRow, ShopRow, ProductRow, OrderRow, MessageRow, AdminStats, ActivityLog, AdminConversation } from '../lib/api';

interface Props {
  user: api.UserRow;
  onLogout: () => void;
}

type Tab = 'stats' | 'users' | 'orders' | 'shops' | 'products' | 'msg-clients' | 'msg-vendors' | 'activity';

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'stats', label: 'Dashboard', icon: '📊' },
  { id: 'users', label: 'Utilisateurs', icon: '👥' },
  { id: 'orders', label: 'Commandes', icon: '📦' },
  { id: 'shops', label: 'Boutiques', icon: '🏪' },
  { id: 'products', label: 'Produits', icon: '🏷️' },
  { id: 'msg-clients', label: 'Messages clients', icon: '💬' },
  { id: 'msg-vendors', label: 'Messages boutiques', icon: '🛒' },
  { id: 'activity', label: 'Journal', icon: '📋' },
];

export function AdminDashboard({ user, onLogout }: Props) {
  const [tab, setTab] = useState<Tab>('stats');
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo"><span>S</span> Spaceness</div>
        <nav className="sidebar-nav">
          {TABS.map((t) => (
            <button key={t.id} className={`sidebar-item ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
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
        {tab === 'stats' && <StatsPage />}
        {tab === 'users' && <UsersPage />}
        {tab === 'orders' && <OrdersPage />}
        {tab === 'shops' && <ShopsPage />}
        {tab === 'products' && <ProductsPage />}
        {tab === 'msg-clients' && <ClientMsgPage />}
        {tab === 'msg-vendors' && <VendorMsgPage />}
        {tab === 'activity' && <ActivityPage />}
      </main>
    </div>
  );
}

/* ===== Dashboard / Stats ===== */
function StatsPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const [s, l] = await Promise.all([api.adminStats(), api.adminActivityLog(5)]);
    if (s.ok) setStats(s);
    if (l.ok) setLogs(l.logs);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Dashboard</h1><p className="page-subtitle">Vue d'ensemble de la plateforme</p></div></div>
      <div className="stats-grid">
        {[
          { label: 'Utilisateurs', value: stats?.users ?? 0, icon: '👥', color: 'blue' },
          { label: 'Boutiques', value: stats?.shops ?? 0, icon: '🏪', color: 'green' },
          { label: 'Produits', value: stats?.products ?? 0, icon: '🏷️', color: 'orange' },
          { label: 'Commandes', value: stats?.orders ?? 0, icon: '📦', color: 'red' },
        ].map((s) => (
          <div key={s.label} className="stat-card">
            <div className={`icon ${s.color}`}>{s.icon}</div>
            <div className="value">{s.value}</div>
            <div className="label">{s.label}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="card-header"><span className="card-title">Activité récente</span></div>
        {logs.length === 0 ? <p className="empty">Aucune activité</p> : (
          <table><thead><tr><th>Action</th><th>Description</th><th>Date</th></tr></thead><tbody>
            {logs.map((l, i) => (
              <tr key={i}><td><strong>{l.action}</strong></td><td>{l.description || '—'}</td><td>{api.formatDate(l.timestamp)}</td></tr>
            ))}
          </tbody></table>
        )}
      </div>
    </>
  );
}

/* ===== Users ===== */
function UsersPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.adminUsers();
    if (res.ok) setUsers(res.users);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    return !q || u.full_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
  });

  const toggleBlock = async (u: UserRow) => {
    const blocked = !u.is_blocked;
    const res = await api.adminBlockUser(u.id, blocked);
    if (res.ok) setUsers((prev) => prev.map((x) => x.id === u.id ? { ...x, is_blocked: blocked ? 1 : 0 } : x));
  };

  const remove = async (u: UserRow) => {
    if (!confirm(`Supprimer ${u.full_name} ? Cette action est irréversible.`)) return;
    const res = await api.adminDeleteUser(u.id);
    if (res.ok) setUsers((prev) => prev.filter((x) => x.id !== u.id));
  };

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header">
        <div><h1 className="page-title">Utilisateurs</h1><p className="page-subtitle">{users.length} comptes au total</p></div>
        <input className="form-input" style={{ maxWidth: 280 }} placeholder="Rechercher..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      <div className="card">
        <table><thead><tr><th>Nom</th><th>Email</th><th>Rôle</th><th>Vérifié</th><th>Statut</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead><tbody>
          {filtered.map((u) => (
            <tr key={u.id}>
              <td><strong>{u.full_name}</strong></td>
              <td>{u.email}</td>
              <td><span className={`badge badge-${u.role === 'admin' ? 'blue' : u.role === 'boutique' ? 'green' : 'gray'}`}>{u.role}</span></td>
              <td>{u.is_verified ? <span className="badge badge-green">Oui</span> : <span className="badge badge-red">Non</span>}</td>
              <td>{u.is_blocked ? <span className="badge badge-red">Bloqué</span> : <span className="badge badge-green">Actif</span>}</td>
              <td style={{ textAlign: 'right' }}>
                {u.role !== 'admin' && (
                  <>
                    <button className="btn btn-ghost btn-sm" onClick={() => toggleBlock(u)} style={{ marginRight: 8 }}>
                      {u.is_blocked ? 'Débloquer' : 'Bloquer'}
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => remove(u)}>Supprimer</button>
                  </>
                )}
              </td>
            </tr>
          ))}
          {filtered.length === 0 && <tr><td colSpan={6} className="empty">Aucun utilisateur trouvé</td></tr>}
        </tbody></table>
      </div>
    </>
  );
}

/* ===== Orders ===== */
function OrdersPage() {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.adminOrders();
    if (res.ok) setOrders(res.orders);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const updateStatus = async (id: number, status: string) => {
    const res = await api.adminUpdateOrderStatus(id, status);
    if (res.ok) setOrders((prev) => prev.map((o) => o.id === id ? { ...o, status } : o));
  };

  const statusBadge = (s: string) => {
    const m: Record<string, string> = { pending: 'orange', shipped: 'blue', delivered: 'green', cancelled: 'red' };
    return <span className={`badge badge-${m[s] || 'gray'}`}>{s}</span>;
  };

  const filtered = orders.filter((o) => {
    const q = search.toLowerCase();
    return !q || String(o.id).includes(q) || (o.client_name || '').toLowerCase().includes(q) || (o.shop_name || '').toLowerCase().includes(q) || (o.product_name || '').toLowerCase().includes(q);
  });

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header">
        <div><h1 className="page-title">Commandes</h1><p className="page-subtitle">{orders.length} commandes au total</p></div>
        <input className="form-input" style={{ maxWidth: 280 }} placeholder="Rechercher..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      <div className="card">
        <table><thead><tr><th>#</th><th>Client</th><th>Produit</th><th>Boutique</th><th>Qté</th><th>Montant</th><th>Statut</th><th>Date</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead><tbody>
          {filtered.map((o) => (
            <tr key={o.id}>
              <td>#{o.id}</td>
              <td>{o.client_name || `#${o.client_user_id}`}</td>
              <td>{o.product_name || `#${o.product_id}`}</td>
              <td>{o.shop_name || '—'}</td>
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
          {filtered.length === 0 && <tr><td colSpan={9} className="empty">Aucune commande</td></tr>}
        </tbody></table>
      </div>
    </>
  );
}

/* ===== Shops ===== */
function ShopsPage() {
  const [shops, setShops] = useState<ShopRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.adminShops();
    if (res.ok) setShops(res.shops);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const remove = async (s: ShopRow) => {
    if (!confirm(`Supprimer la boutique "${s.shop_name}" ? Tous les produits seront supprimés.`)) return;
    const res = await api.adminDeleteShop(s.id);
    if (res.ok) setShops((prev) => prev.filter((x) => x.id !== s.id));
  };

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Boutiques</h1><p className="page-subtitle">{shops.length} boutiques enregistrées</p></div></div>
      <div className="card">
        <table><thead><tr><th>Nom</th><th>Propriétaire</th><th>Email</th><th>Description</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead><tbody>
          {shops.map((s) => (
            <tr key={s.id}>
              <td><strong>{s.shop_name}</strong></td>
              <td>{s.owner_name || '—'}</td>
              <td>{s.owner_email || '—'}</td>
              <td style={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.description || '—'}</td>
              <td style={{ textAlign: 'right' }}><button className="btn btn-danger btn-sm" onClick={() => remove(s)}>Supprimer</button></td>
            </tr>
          ))}
          {shops.length === 0 && <tr><td colSpan={5} className="empty">Aucune boutique</td></tr>}
        </tbody></table>
      </div>
    </>
  );
}

/* ===== Products ===== */
function ProductsPage() {
  const [products, setProducts] = useState<ProductRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.adminProducts();
    if (res.ok) setProducts(res.products);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const remove = async (p: ProductRow) => {
    if (!confirm(`Supprimer "${p.name}" ?`)) return;
    const res = await api.adminDeleteProduct(p.id);
    if (res.ok) setProducts((prev) => prev.filter((x) => x.id !== p.id));
  };

  const filtered = products.filter((p) => {
    const q = search.toLowerCase();
    return !q || p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q) || (p.shop_name || '').toLowerCase().includes(q);
  });

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header">
        <div><h1 className="page-title">Produits</h1><p className="page-subtitle">{products.length} produits au total</p></div>
        <input className="form-input" style={{ maxWidth: 280 }} placeholder="Rechercher..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      <div className="card">
        <table><thead><tr><th>Nom</th><th>Catégorie</th><th>Prix</th><th>Stock</th><th>Boutique</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead><tbody>
          {filtered.map((p) => (
            <tr key={p.id}>
              <td><strong>{p.name}</strong></td>
              <td><span className="badge badge-blue">{p.category}</span></td>
              <td>{api.formatPrice(p.price)}</td>
              <td>{p.stock > 0 ? <span className="badge badge-green">{p.stock}</span> : <span className="badge badge-red">Rupture</span>}</td>
              <td>{p.shop_name || `#${p.shop_id}`}</td>
              <td style={{ textAlign: 'right' }}><button className="btn btn-danger btn-sm" onClick={() => remove(p)}>Supprimer</button></td>
            </tr>
          ))}
          {filtered.length === 0 && <tr><td colSpan={6} className="empty">Aucun produit</td></tr>}
        </tbody></table>
      </div>
    </>
  );
}

/* ===== Client Messages ===== */
function ClientMsgPage() {
  const [conversations, setConversations] = useState<AdminConversation[]>([]);
  const [messages, setMessages] = useState<MessageRow[]>([]);
  const [activeUserId, setActiveUserId] = useState<number | null>(null);
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const loadConvos = useCallback(async () => {
    setLoading(true);
    const res = await api.adminClientConversations();
    if (res.ok) setConversations(res.conversations);
    setLoading(false);
  }, []);

  useEffect(() => { loadConvos(); }, [loadConvos]);

  const openConvo = async (userId: number) => {
    setActiveUserId(userId);
    const res = await api.adminClientConversation(userId);
    if (res.ok) setMessages(res.messages);
  };

  const handleReply = async () => {
    if (!reply.trim() || messages.length === 0) return;
    setSending(true);
    const target = messages[0];
    await api.adminReplyMessage(target.id, reply.trim());
    setReply('');
    setSending(false);
    if (activeUserId) openConvo(activeUserId);
  };

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Messages clients</h1><p className="page-subtitle">{conversations.length} conversations</p></div></div>
      <div style={{ display: 'flex', gap: 16 }}>
        <div className="card" style={{ width: 280, flexShrink: 0 }}>
          <div className="card-header"><span className="card-title">Conversations</span></div>
          <div style={{ maxHeight: 500, overflowY: 'auto' }}>
            {conversations.map((c) => (
              <div key={c.user_id} onClick={() => c.user_id && openConvo(c.user_id)} style={{ padding: '12px 16px', cursor: 'pointer', borderBottom: '1px solid var(--border)', background: activeUserId === c.user_id ? 'var(--primary-light)' : 'transparent' }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{c.full_name || `Utilisateur #${c.user_id}`}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.last_message || c.email}</div>
              </div>
            ))}
            {conversations.length === 0 && <p className="empty">Aucune conversation</p>}
          </div>
        </div>
        <div className="card" style={{ flex: 1 }}>
          {!activeUserId ? (
            <div className="empty" style={{ padding: 80 }}>Sélectionnez une conversation</div>
          ) : (
            <div>
              <div className="card-header"><span className="card-title">Messages</span></div>
              <div style={{ padding: 16, maxHeight: 400, overflowY: 'auto' }}>
                {messages.map((m) => (
                  <div key={m.id} style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{api.formatDate(m.created_at)} — <strong>{m.subject}</strong></div>
                    <div style={{ padding: '8px 12px', background: 'var(--bg)', borderRadius: 8, marginTop: 4, fontSize: 14 }}>{m.message}</div>
                    {m.admin_reply && (
                      <div style={{ padding: '8px 12px', background: 'var(--primary-light)', borderRadius: 8, marginTop: 4, fontSize: 14, color: 'var(--primary)' }}>
                        <strong>Réponse :</strong> {m.admin_reply}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div style={{ padding: 16, borderTop: '1px solid var(--border)' }}>
                <textarea className="form-input" value={reply} onChange={(e) => setReply(e.target.value)} placeholder="Votre réponse..." />
                <button className="btn btn-primary" style={{ marginTop: 8 }} disabled={!reply.trim() || sending} onClick={handleReply}>
                  {sending ? 'Envoi...' : 'Répondre'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/* ===== Vendor Messages ===== */
function VendorMsgPage() {
  const [conversations, setConversations] = useState<AdminConversation[]>([]);
  const [messages, setMessages] = useState<MessageRow[]>([]);
  const [activeShopId, setActiveShopId] = useState<number | null>(null);
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const loadConvos = useCallback(async () => {
    setLoading(true);
    const res = await api.adminShopConversations();
    if (res.ok) setConversations(res.conversations);
    setLoading(false);
  }, []);

  useEffect(() => { loadConvos(); }, [loadConvos]);

  const openConvo = async (shopId: number) => {
    setActiveShopId(shopId);
    const res = await api.adminShopConversation(shopId);
    if (res.ok) setMessages(res.messages);
  };

  const handleReply = async () => {
    if (!reply.trim() || messages.length === 0) return;
    setSending(true);
    const target = messages.find((m) => m.shop_id);
    if (target) await api.adminReplyVendorMessage(target.id, reply.trim());
    setReply('');
    setSending(false);
    if (activeShopId) openConvo(activeShopId);
  };

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Messages boutiques</h1><p className="page-subtitle">{conversations.length} conversations</p></div></div>
      <div style={{ display: 'flex', gap: 16 }}>
        <div className="card" style={{ width: 280, flexShrink: 0 }}>
          <div className="card-header"><span className="card-title">Conversations</span></div>
          <div style={{ maxHeight: 500, overflowY: 'auto' }}>
            {conversations.map((c) => (
              <div key={c.shop_id} onClick={() => c.shop_id && openConvo(c.shop_id)} style={{ padding: '12px 16px', cursor: 'pointer', borderBottom: '1px solid var(--border)', background: activeShopId === c.shop_id ? 'var(--primary-light)' : 'transparent' }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{c.shop_name || `Boutique #${c.shop_id}`}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{c.last_message || '—'}</div>
              </div>
            ))}
            {conversations.length === 0 && <p className="empty">Aucune conversation</p>}
          </div>
        </div>
        <div className="card" style={{ flex: 1 }}>
          {!activeShopId ? (
            <div className="empty" style={{ padding: 80 }}>Sélectionnez une conversation</div>
          ) : (
            <div>
              <div className="card-header"><span className="card-title">Messages</span></div>
              <div style={{ padding: 16, maxHeight: 400, overflowY: 'auto' }}>
                {messages.map((m) => (
                  <div key={m.id} style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{api.formatDate(m.created_at)} — <strong>{m.subject}</strong> ({m.is_from_vendor ? 'boutique' : 'admin'})</div>
                    <div style={{ padding: '8px 12px', background: m.is_from_vendor ? 'var(--bg)' : 'var(--primary-light)', borderRadius: 8, marginTop: 4, fontSize: 14 }}>{m.message}</div>
                    {m.admin_reply && (
                      <div style={{ padding: '8px 12px', background: 'var(--success-light)', borderRadius: 8, marginTop: 4, fontSize: 14, color: 'var(--success)' }}>
                        <strong>Réponse :</strong> {m.admin_reply}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div style={{ padding: 16, borderTop: '1px solid var(--border)' }}>
                <textarea className="form-input" value={reply} onChange={(e) => setReply(e.target.value)} placeholder="Votre réponse..." />
                <button className="btn btn-primary" style={{ marginTop: 8 }} disabled={!reply.trim() || sending} onClick={handleReply}>
                  {sending ? 'Envoi...' : 'Répondre'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/* ===== Activity Log ===== */
function ActivityPage() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.adminActivityLog(200);
    if (res.ok) setLogs(res.logs);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="loader">Chargement...</div>;

  return (
    <>
      <div className="page-header"><div><h1 className="page-title">Journal d'activité</h1><p className="page-subtitle">{logs.length} événements récents</p></div></div>
      <div className="card">
        <table><thead><tr><th>Action</th><th>Description</th><th>Date</th></tr></thead><tbody>
          {logs.map((l, i) => (
            <tr key={i}><td><strong>{l.action}</strong></td><td>{l.description || '—'}</td><td>{api.formatDate(l.timestamp)}</td></tr>
          ))}
          {logs.length === 0 && <tr><td colSpan={3} className="empty">Aucun journal</td></tr>}
        </tbody></table>
      </div>
    </>
  );
}