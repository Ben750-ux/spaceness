# Spaceness — Application Mobile Marketplace

## C'est quoi ce projet ?

C'est une **application de vente en ligne** (comme un petit Amazon) avec :
- Une **app mobile** (Kivy) que tu lances sur ton PC
- Un **serveur en ligne** (API) qui gère les données
- Une **base de données** qui stocke tout

---

## Comment ça marche ? (explication simple)

```
Toi (utilisateur)
      │
      ▼
┌─────────────────────┐
│   App Kivy (mobile) │ ← Ce que tu vois et touches
│   main.py           │
└─────────┬───────────┘
          │ ❶ Tu cliques sur "Connexion"
          │ ❷ L'app envoie une requête HTTP
          ▼
┌─────────────────────┐
│   Serveur API       │ ← Le "cerveau" qui réfléchit
│   FastAPI           │
│   backend/main.py   │
└─────────┬───────────┘
          │ ❸ Le serveur vérifie le mot de passe
          │ ❹ Il répond "OK" ou "Erreur"
          ▼
┌─────────────────────┐
│   Base de données   │ ← La "mémoire" qui stocke tout
│   PostgreSQL        │
│   (dans le cloud)   │
└─────────────────────┘
```

**Concrètement :**
- Tout le monde voit les **mêmes produits**, les **mêmes prix**
- Si tu achètes un article, le stock diminue pour **tout le monde**
- Tu peux fermer l'app, rouvrir : tes données sont **toujours là**
- Ton ami peut installer l'app chez lui et **voir les mêmes produits**

---

## Les différents morceaux du projet

### 📱 `main.py` — L'application mobile
- C'est l'écran que tu vois quand tu lances `python main.py`
- Gère : l'affichage, les boutons, les menus, le panier
- **Ne stocke RIEN** — elle demande tout au serveur
- Fichier principal : `main.py`

### 📡 `api_client.py` — Le traducteur
- C'est le "téléphone" de l'app
- Chaque action (connexion, achat, recherche) est transformée en requête HTTP
- Envoie les messages au serveur et reçoit les réponses
- Point d'entrée : `https://spaceness.onrender.com`

### 🧠 `backend/` — Le serveur (API)
- C'est le cerveau, il tourne 24h/24 sur Render (serveur en ligne)
- Reçoit les requêtes de l'app mobile
- Vérifie si le mot de passe est bon
- Ajoute les produits au panier
- Enregistre les commandes
- Contient plusieurs fichiers :

| Fichier | Rôle |
|---------|------|
| `main.py` | Les "portes" de l'API (les adresses `/api/login`, `/api/products`...) |
| `models.py` | La description des tables (un utilisateur a un nom, un email...) |
| `crud.py` | Les actions possibles (créer un utilisateur, ajouter un produit...) |
| `config.py` | Les réglages (adresse de la base de données...) |
| `start.py` | Le bouton "ON" du serveur |

### 🗄️ PostgreSQL (Neon.tech) — La base de données
- C'est la mémoire, elle tourne dans le cloud (Neon.tech)
- Stocke TOUTES les données sous forme de tableaux :

```
📋 Table "users"
┌────┬───────────┬──────────────────┬──────────┐
│ ID │   Nom     │    Email         │  Rôle    │
├────┼───────────┼──────────────────┼──────────┤
│ 1  │ Admin     │ admin@shop.local │ admin    │
│ 2  │ Tech Shop │ tech@shop.local  │ boutique │
│ 3  │ Jean      │ jean@email.com   │ client   │
└────┴───────────┴──────────────────┴──────────┘

📋 Table "products"
┌────┬──────────────────┬──────────┬───────┬───────┐
│ ID │     Nom          │ Catégorie│ Prix  │ Stock │
├────┼──────────────────┼──────────┼───────┼───────┤
│ 1  │ Écouteurs Bluetooth │ Tech  │ 29.99 │  20   │
│ 2  │ T-shirt Premium  │ Mode     │ 18.00 │  50   │
└────┴──────────────────┴──────────┴───────┴───────┘
```

### 🖥️ `admin/` — Les dashboards web
- Ce sont des pages web (HTML/JS) pour gérer le site
- **Dashboard admin** : voir tous les utilisateurs, bloquer, supprimer
- **Dashboard boutique** : gérer ses produits, voir ses commandes
- Accessibles sur http://localhost:5000 et http://localhost:5001

---

## Comment lancer le projet

### Avec le serveur en ligne (RECOMMANDÉ)
```powershell
pip install -r requirements.txt
python main.py
```
✅ Aucune configuration. Tout est déjà connecté.

### En local (pour développer sans internet)
```powershell
# Terminal 1 : Démarrer le serveur
cd backend
..\.venv\Scripts\uvicorn main:app --reload --port 8000

# Terminal 2 : Démarrer l'app
$env:API_URL="http://127.0.0.1:8000"
python main.py
```

---

## Comptes de test (déjà créés automatiquement)

| Qui ? | Email | Mot de passe |
|-------|-------|-------------|
| 🔑 **Admin** (gère tout) | `admin@shop.local` | `admin123` |
| 🏪 **Boutique Tech** (vend des gadgets) | `tech@shop.local` | `vendor123` |
| 🏪 **Maison Mode** (vend des vêtements) | `mode@shop.local` | `vendor123` |

Tu peux aussi créer ton propre compte client depuis l'app.

---

## Erreur "Failed to load image <https://picsum.photos/...>"

**Pas d'inquiétude, ce n'est pas une erreur grave.**

`picsum.photos` est un site qui génère des images aléatoires. Il est utilisé pour les **photos de démonstration** des produits et des boutiques. 

**Pourquoi ça plante ?** Le site `picsum.photos` n'est pas accessible depuis ta connexion internet (timeout). Les images ne s'affichent pas, mais **tout le reste marche parfaitement**.

**Solution simple :** On peut remplacer les URLs des images par des images locales. Tu veux que je le fasse ?

---

## Déploiement : comment ça a été mis en ligne ?

### 1. Neon.tech (Base de données gratuite)
- PostgreSQL gratuit (500 Mo)
- Stocke toutes les données dans le cloud
- Accessible uniquement par le serveur

### 2. Render (Serveur gratuit)
- Héberge le backend FastAPI
- Gratuit mais se met en veille après 15 min sans activité
- Au premier clic, ça prend ~30s à se réveiller
- URL : `https://spaceness.onrender.com`

### 3. GitHub (Stockage du code)
- Le code source est sur GitHub
- Render lit le code depuis GitHub et le déploie automatiquement

---

## Structure complète du projet

```
spaceness/
│
├── main.py              # App mobile Kivy
├── app.kv               # Design de l'app (fichier Kivy)
├── api_client.py        # Connecteur vers le serveur
├── database.py          # Ancienne version locale (conservée)
│
├── backend/             # ⬅️ Le serveur
│   ├── main.py          #   Les routes de l'API
│   ├── models.py        #   Les tables de données
│   ├── crud.py          #   Les actions sur les données
│   ├── config.py        #   Les réglages
│   └── ...              #   Migrations, etc.
│
├── admin/               # Dashboards web
│   ├── api.py           #   Interface admin
│   └── static/          #   Pages HTML
│
└── README.md            # Ce fichier
```

---

## Liste des actions possibles (API)

### Compte
- ✅ Créer un compte → `POST /api/auth/register`
- ✅ Se connecter → `POST /api/auth/login`
- ✅ Voir mon profil → `POST /api/auth/get-user`

### Produits
- ✅ Voir tous les produits → `GET /api/products`
- ✅ Chercher un produit → `GET /api/products?search=tshirt`
- ✅ Filtrer par catégorie → `GET /api/products?category=Mode`
- ✅ Détail d'un produit → `GET /api/products/1`
- ✅ Ajouter un produit (boutique) → `POST /api/products/add`

### Commandes
- ✅ Passer commande → `POST /api/orders/place`
- ✅ Voir mes commandes → `GET /api/orders/client/1`
- ✅ Suivi du statut → champ `status` dans la commande

### Favoris
- ✅ Ajouter aux favoris → `POST /api/favorites/add`
- ✅ Voir mes favoris → `GET /api/favorites/1`
- ✅ Supprimer un favori → `POST /api/favorites/remove`

### Autres
- ✅ Noter un produit → `POST /api/reviews/add`
- ✅ S'abonner à une boutique → `POST /api/subscriptions/subscribe`
- ✅ Contacter l'admin → `POST /api/messages/send`

Documentation interactive : [https://spaceness.onrender.com/docs](https://spaceness.onrender.com/docs)

---

## Ce qui a changé (récap simple)

| Avant (PC seulement) | Maintenant (partout) |
|---------------------|---------------------|
| Base de données dans un fichier | Base de données sur Internet |
| Perds tout si tu changes de PC | Retrouves tout partout |
| Toi tout seul | Plusieurs personnes peuvent se connecter |
| Pas de vrai backend | Serveur professionnel 24h/24 |
| Images qui viennent d'internet (picsum) | Images à mettre en local |

---

## Dépannage rapide

**"L'app rame au démarrage"** → C'est normal, Render se réveille (30s max).

**"Les images ne s'affichent pas"** → picsum.photos est bloqué. On peut les remplacer par des images locales.

**"Erreur de connexion au serveur"** → Vérifie que `api_client.py` a `API_URL = "https://spaceness.onrender.com"`.

**"Je veux travailler hors-ligne"** → Lance le serveur local (voir section "En local").
