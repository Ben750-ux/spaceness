# Spaceness — Application Mobile Marketplace

Application mobile de vente en ligne avec backend asynchrone (FastAPI + PostgreSQL), dashboards web administrateur et boutique.

---

## Architecture

```
📱 App Mobile (Kivy/KivyMD)
   │
   │  HTTP (JSON)
   │  api_client.py → API_URL
   ▼
🌐 Backend FastAPI (Render / en ligne)
   │  https://spaceness.onrender.com
   │
   │  SQLAlchemy 2.0 (async)
   │  asyncpg (driver PostgreSQL)
   ▼
🗄️ PostgreSQL (Neon.tech / cloud)
     ┌──────────────────────┐
     │ users                │
     │ shops                │
     │ products             │
     │ orders               │
     │ favorites            │
     │ product_reviews      │
     │ shop_subscriptions   │
     │ view_history         │
     │ admin_messages       │
     │ vendor_admin_messages│
     │ app_settings         │
     │ login_attempts       │
     │ activity_log         │
     └──────────────────────┘
```

L'application mobile **ne parle jamais directement à la base de données**. Elle passe toujours par l'API REST FastAPI.

---

## Fonctionnalités

### Utilisateurs
- Authentification obligatoire (connexion + inscription)
- Trois rôles : `client`, `boutique`, `admin`
- Session persistante (auto-connexion)
- Inscription publique (rôle `client` uniquement)
- Vérification par code (email simulé)
- Blocage de compte par l'administration

### Marketplace
- Catalogue principal avec recherche et filtres par catégorie
- Fiche produit détaillée (images multiples, description, stock, avis)
- Système de favoris avec heart icon
- Historique des produits consultés
- Système d'avis et notes (1-5 étoiles)

### Panier & Commandes
- Panier multi-articles avec checkout global
- Monnaie de test en crédits
- Suivi des commandes avec statuts colorés
- Commandes accessibles depuis "Mes commandes"

### Abonnements
- Les clients peuvent s'abonner aux boutiques
- Flux des nouveaux produits des boutiques abonnées

### Dashboard Admin (web)
- Interface web séparée
- Statistiques globales (utilisateurs, produits, ventes)
- Gestion des utilisateurs (bloquer/débloquer/supprimer)
- Gestion des produits et boutiques
- Gestion des commandes (changement de statut)
- Messagerie avec les clients et les boutiques
- Journal d'activité

### Dashboard Boutique (web)
- Interface web pour les vendeurs
- Statistiques de la boutique
- Gestion des produits (CRUD)
- Gestion des commandes reçues
- Messagerie avec l'administration

---

## Déploiement (ce qui a été mis en place)

### Base de données (Neon.tech)
- PostgreSQL 16 gratuit (0.5 GB)
- SSL requis
- Gère les accès concurrents
- Backup automatique

### Backend API (Render)
- FastAPI avec Python 3.12
- Routes asynchrones (async/await)
- SQLAlchemy 2.0 avec sessions async
- Auto-scaling (gratuit, sleep après inactivité)
- Délai de réveil : ~30s (free tier)

### Lien entre l'app et le backend
- `api_client.py` envoie des requêtes HTTP vers `API_URL`
- Par défaut : `https://spaceness.onrender.com`
- Surchargeable avec la variable d'environnement `API_URL`

---

## Lancer le projet

### 1. Application mobile (avec le backend en ligne)

```powershell
pip install -r requirements.txt
python main.py
```

Par défaut, l'app utilise le backend déployé sur Render. **Aucune configuration supplémentaire nécessaire.**

### 2. Application mobile (en local pour le développement)

```powershell
# Terminal 1 : backend local
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///test.db"
uvicorn main:app --reload --port 8000

# Terminal 2 : app Kivy
$env:API_URL="http://127.0.0.1:8000"
python main.py
```

### 3. Dashboards web (admin / boutique)

```powershell
# Dashboard admin
python admin\api.py
# → http://localhost:5000

# Dashboard boutique
python admin\vendor_api.py
# → http://localhost:5001
```

---

## Comptes de test (pré-remplis automatiquement)

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| **Admin** | `admin@shop.local` | `admin123` |
| **Boutique** | `tech@shop.local` | `vendor123` |
| **Boutique** | `mode@shop.local` | `vendor123` |

---

## Structure du projet

```
spaceness/
├── main.py                    # App Kivy (écrans, logique métier)
├── app.kv                     # Interface Kivy (layouts KivyMD)
├── api_client.py              # Client HTTP vers l'API REST
├── database.py                # Ancienne couche SQLite (local)
├── requirements.txt           # Dépendances Kivy
│
├── backend/                   # ⬅️ NOUVEAU : Backend FastAPI
│   ├── main.py                #   API FastAPI (routes)
│   ├── models.py              #   Modèles SQLAlchemy (tables)
│   ├── crud.py                #   Opérations CRUD asynchrones
│   ├── config.py              #   Configuration (variables env)
│   ├── database.py            #   Ancienne version SQLite (conservée)
│   ├── start.py               #   Point d'entrée Render
│   ├── requirements.txt       #   Dépendances backend
│   ├── Procfile               #   Configuration Render
│   ├── runtime.txt            #   Version Python Render
│   ├── alembic.ini            #   Configuration migrations
│   ├── alembic/               #   Migrations de base
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial.py
│   └── README.md
│
├── admin/                     # Dashboards web (Flask)
│   ├── api.py                 #   API admin
│   ├── vendor_api.py          #   API boutique
│   ├── static/                #   Dashboard admin (HTML/JS/CSS)
│   └── vendor/                #   Dashboard boutique (HTML/JS/CSS)
│
├── .env.example               # Variables d'environnement (template)
├── .gitignore
└── README.md
```

---

## API REST — Endpoints principaux

### Authentification
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/auth/register` | Créer un compte |
| POST | `/api/auth/login` | Connexion |
| POST | `/api/auth/verify-code` | Vérifier email |
| POST | `/api/auth/get-user` | Infos utilisateur |

### Produits
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/products` | Liste des produits (recherche + catégorie) |
| GET | `/api/products/{id}` | Détail d'un produit |
| GET | `/api/shops/{id}/products` | Produits d'une boutique |
| POST | `/api/products/add` | Ajouter un produit (boutique) |
| POST | `/api/products/update-stock` | Modifier stock |

### Commandes
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/orders/place` | Passer une commande |
| GET | `/api/orders/client/{id}` | Commandes d'un client |
| POST | `/api/orders/update-status` | Mettre à jour le statut |

### Favoris & Historique
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/favorites/add` | Ajouter aux favoris |
| POST | `/api/favorites/remove` | Retirer des favoris |
| GET | `/api/favorites/{id}` | Lister les favoris |
| POST | `/api/history/add` | Ajouter à l'historique |

### Avis
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/reviews/add` | Ajouter/modifier un avis |
| GET | `/api/reviews/{id}` | Avis d'un produit |

### Abonnements
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/subscriptions/subscribe` | S'abonner à une boutique |
| POST | `/api/subscriptions/unsubscribe` | Se désabonner |

### Administration
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/admin/stats` | Statistiques globales |
| GET | `/api/admin/users` | Liste des utilisateurs |
| GET | `/api/admin/orders` | Toutes les commandes |
| POST | `/api/admin/users/block` | Bloquer/débloquer un utilisateur |

Documentation interactive : [https://spaceness.onrender.com/docs](https://spaceness.onrender.com/docs)

---

## Migrations (Alembic)

Si tu modifies les modèles, génère une migration :

```powershell
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## Ce qui a changé (SQLite → PostgreSQL)

| Aspect | Avant (SQLite) | Maintenant (PostgreSQL) |
|--------|---------------|------------------------|
| Stockage | Fichier `shop.db` local | Base de données cloud |
| Accès concurrents | ❌ Non supporté | ✅ Transactions ACID |
| Synchronisation | ❌ Aucune | ✅ En ligne, temps réel |
| Déploiement | ❌ Local uniquement | ✅ Render + Neon.tech |
| ORM | SQL brut | ✅ SQLAlchemy 2.0 async |
| Types avancés | ❌ Limitée | ✅ JSON, arrays, enum |
| Sécurité | ❌ Aucune | ✅ SSL, hachage, rôles |
| Migrations | ❌ Manuelles | ✅ Alembic automatique |

---

## Dépannage

### Le backend Render ne répond pas
Render free tier **se met en veille** après 15 min d'inactivité. La première requête prend ~30s le temps qu'il se réveille. Pas d'inquiétude.

### Erreur de connexion à la base de données
Vérifie que la variable `DATABASE_URL` est correcte dans les variables d'environnement Render.

### L'app Kivy utilise toujours la base locale
Vérifie que `API_URL` pointe bien vers `https://spaceness.onrender.com` (dans `api_client.py` ou variable d'environnement).

---

## Prochaines améliorations possibles

- Paiement réel (mobile money / carte)
- Génération APK Android (Buildozer)
- Notifications push
- Chat client-boutique en temps réel (WebSocket)
- Images uploadées (via Cloudinary/S3)
- Cache Redis pour les performances
- Tests automatisés (pytest)
