# Spaceness - Application Mobile Marketplace (KivyMD + SQLite)

Application mobile de vente en ligne avec authentification, panier, commandes et dashboard administrateur.

## Fonctionnalités

### Utilisateurs
- Authentification obligatoire (connexion + inscription)
- Trois rôles : `client`, `boutique`, `admin`
- Session persistante (auto-connexion)
- Inscription publique (rôle `client` uniquement)

### Marketplace
- Catalogue principal avec recherche et filtres par catégorie
- Fiche produit détaillée (images multiples, description, stock, avis)
- Système de favoris avec heart icon
- Historique des produits consultés
- Système d'avis et notes (1-5 étoiles)

### Panier & Commandes
- Panier multi-articles avec checkout global
- Monnaie de test en credits
- Suivi des commandes avec statuts colorés
- Commandes accessibles depuis "Mes commandes"

### Dashboard Admin
- Dashboard web accessible via navigateur
- API Flask REST pour la gestion
- Voir les statistiques globales
- Gérer les utilisateurs (bloquer/débloquer/supprimer)
- Gérer les produits (supprimer)
- Gérer les boutiques (supprimer)
- Gérer les commandes (changer le statut)

## Lancer le projet

### Application mobile
```powershell
cd "C:\Users\DELL\Documents\kivy_shop_app"
pip install -r requirements.txt
python main.py
```

### Dashboard Admin (web)
```powershell
cd "C:\Users\DELL\Documents\kivy_shop_app"
.venv\Scripts\python.exe admin\api.py
```
Puis ouvrir : http://localhost:5000

## Comptes de test

- **Admin** : `admin@shop.local` / `admin123`
- **Vendeur** : `tech@shop.local` / `vendor123`
- **Client** : Créez un compte depuis l'application

## Sécurité

- Hash du mot de passe avec salt (sha256)
- Requêtes SQL paramétrées (anti-injections)
- Vérification des rôles en base
- Blocage de compte utilisateur

## Structure du projet

```
kivy_shop_app/
├── main.py           # Application Kivy (écrans, logique)
├── app.kv           # Interface Kivy (layouts, widgets)
├── database.py      # Base de données SQLite
├── requirements.txt # Dépendances Python
├── shop.db         # Base de données (générée)
├── session.json    # Session utilisateur
├── admin/
│   ├── api.py      # API Flask REST
│   └── static/
│       ├── index.html  # Dashboard HTML
│       ├── style.css   # Styles CSS
│       └── app.js      # JavaScript
└── README.md       # Documentation
```

## Prochaines améliorations

- Paiement réel (mobile money / carte)
- Génération APK Android (Buildozer)
- Notifications push
- Chat client-boutique
