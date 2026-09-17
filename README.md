# Spaceness — MarketPlace de Lubumbashi

Application de vente en ligne : app mobile (React Native/Expo) et API FastAPI hébergée sur Render.
Les dashboards web (admin + boutique) sont séparés dans un autre dossier : `C:\Users\DELL\Documents\spaceness-dashboard`.

## Structure du projet

```
├── backend/            API FastAPI (production : https://spaceness.onrender.com)
├── mobile/             App mobile React Native (Expo)
└── (hors repo)         Dashboards dans Documents\spaceness-dashboard\
```

## App mobile

```bash
cd mobile
npm.cmd start -- --web              # tester sur PC (navigateur)
npm.cmd start                       # tester sur téléphone via Expo Go
npm.cmd exec tsc -- --noEmit        # vérifier les types
```

## Dashboards (dossier séparé)

Voir `C:\Users\DELL\Documents\spaceness-dashboard\` :

- `dashboard-admin/`   → port 5000 (admin) — `admin@shop.local` / `admin123`
- `dashboard-vendor/`  → port 5001 (boutique) — `tech@shop.local` / `vendor123`

```bash
cd dashboard-admin
npm.cmd install --legacy-peer-deps
npm.cmd run dev

cd ../dashboard-vendor
npm.cmd install --legacy-peer-deps
npm.cmd run dev
```