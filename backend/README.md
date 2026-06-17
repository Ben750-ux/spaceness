# Backend Spaceness

API REST FastAPI avec PostgreSQL asynchrone (SQLAlchemy 2.0 + asyncpg)

## Prérequis

- Python 3.12+
- PostgreSQL (ou SQLite pour le dev local)

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` vers `.env` et ajuster :

```bash
# Pour PostgreSQL (production)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/spaceness

# Pour SQLite (dev local)
DATABASE_URL=sqlite+aiosqlite:///shop.db
```

## Lancement

```bash
# Dev avec rechargement auto
uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Migrations (Alembic)

```bash
# Créer une migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head

# Annuler la dernière migration
alembic downgrade -1
```

## Déploiement

### Render / Railway

1. Créer un PostgreSQL (Railway le fait automatiquement)
2. Configurer la variable d'environnement `DATABASE_URL`
3. Déployer depuis GitHub

### Variables d'environnement

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL de connexion PostgreSQL |
| `PORT` | Port du serveur (défaut: 8000) |
| `SECRET_KEY` | Clé secrète pour sessions |
| `CORS_ORIGINS` | Origines CORS autorisées |

## API

Documentation automatique : http://localhost:8000/docs
