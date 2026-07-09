# Tradfolk

Tradfolk est une application de vote "Trad ou Folk ?".

Le frontend affiche des cartes à swiper.
Le backend enregistre les votes et calcule les statistiques en temps réel.

## Stack technique

- Frontend: Vue 3 + Vite + Axios
- Backend: Flask + SQLAlchemy + Alembic + Gunicorn
- Base de données: PostgreSQL
- Reverse proxy local: Traefik (HTTPS local)
- Conteneurisation: Docker Compose

## Architecture

- Frontend: [frontend](frontend)
- Backend: [backend](backend)
- Migrations SQL: [backend/migrations/versions](backend/migrations/versions)
- Données initiales des propositions: [proposals.json](proposals.json)
- Orchestration locale: [docker-compose.yml](docker-compose.yml)
- Override dev: [docker-compose.dev.yml](docker-compose.dev.yml)

## Prérequis

- Docker
- Docker Compose

## Installation rapide (local)

Copier le fichier d'environnement et le mettre à jour:

```bash
cp .env.dist .env
```

Ajouter les hosts locaux (si nécessaire):

 ```text
 127.0.0.1 tradfolk.local
 127.0.0.1 api.tradfolk.local
 ```

Lancer la stack:

```bash
docker compose up --build
```

Pour un pilotage automatique via APP_ENV (dev/prod), utiliser plutôt:

```bash
make up
```

Ouvrir l'application:

- App: <https://tradfolk.local>
- API: <https://api.tradfolk.local>

Note: Traefik génère un certificat local auto-signé. Le navigateur peut afficher un avertissement la première fois.

## Fonctionnement au démarrage

Au démarrage du conteneur backend, le script [backend/scripts/entrypoint.sh](backend/scripts/entrypoint.sh):

1. Attend la disponibilité PostgreSQL
2. Exécute les migrations Alembic
3. Importe les propositions depuis [proposals.json](proposals.json)
4. Lance Gunicorn

## Configuration

Variables principales dans [.env.dist](.env.dist):

- APP_ENV: mode d'exécution global (prod ou dev)
- API_URL: URL backend utilisée au build du frontend
- POSTGRES_*: paramètres de connexion DB
- SECRET_KEY: clé de signature backend (cookies d'origine)
- CORS_ORIGINS: unique origine autorisée côté API (mettre l'URL de l'app)
- TRAEFIK_*: ports et règles d'exposition locale

### APP_ENV et comportements

- `APP_ENV=prod`:
  - Frontend servi par Nginx (build statique)
  - Backend Gunicorn mode standard
  - Logs Traefik/Gunicorn configurables via variables dédiées
- `APP_ENV=dev` (avec `make up`):
  - Frontend en mode Vite watch/HMR
  - Backend en mode Gunicorn `--reload` + logs debug
  - Montages de code source pour itération locale

Exemple dev dans `.env`:

```env
APP_ENV=dev
TRAEFIK_LOG_LEVEL=DEBUG
GUNICORN_LOG_LEVEL=debug
```

Exemple prod dans `.env`:

```env
APP_ENV=prod
TRAEFIK_LOG_LEVEL=INFO
GUNICORN_LOG_LEVEL=info
```

Recommandations:

- Changer SECRET_KEY pour toute exécution non locale
- Garder des origines CORS explicites
- Éviter d'exposer la stack telle quelle sur Internet sans hardening supplémentaire

## Données des propositions

- Source: [proposals.json](proposals.json)
- Schéma attendu par l'import:

```json
[
  {
    "id": "{uuid}",
    "label": "{Libellé de la proposition}",
    "image": "{URL de l'image associée à la proposition}",
    "active": true
  }
]
```

Le backend persiste le champ label dans la colonne SQL libelle pour compatibilité du modèle actuel.

## Commandes utiles

Depuis la racine du projet:

- Lint global:

```bash
make lint
```

- Format global:

```bash
make format
```

- Vérifications globales:

```bash
make check
```

- Build des images backend/frontend:

```bash
make build-images
```

### Frontend seulement

- Dossier: [frontend](frontend)
- Scripts disponibles: voir [frontend/package.json](frontend/package.json)

Exemples:

```bash
cd frontend
npm install
npm run dev
npm run check
```

### Backend seulement

- Dossier: [backend](backend)

Exemples:

```bash
cd backend
pip install -r requirements-dev.txt
ruff check app migrations
python -m compileall app migrations
```

## API (résumé)

Endpoints principaux dans [backend/app/main.py](backend/app/main.py):

- GET /health
- GET /proposals/random
- GET /progress
- POST /votes
- GET /results

L'API applique:

- Rate limiting par origine/IP
- Validation de payload sur /votes
- Cookie d'origine signé (httponly, secure, samesite=lax)

## Migrations

- Migration initiale unique: [backend/migrations/versions/0001_init.py](backend/migrations/versions/0001_init.py)

Pour appliquer:

```bash
cd backend
alembic upgrade head
```

## Réinitialiser complètement la base locale

Si tu veux repartir de zéro:

1. Arrêter les services:

```bash
docker compose down
```

1. Supprimer les données locales Postgres:

```bash
rm -rf postgres-data
```

1. Relancer:

```bash
docker compose up --build
```

## CI

Workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)

Jobs:

- quality: installe les dépendances puis lance lint + check
- docker-build: build des images backend/frontend

## Dépannage

- HTTPS local inaccessible:
  - vérifier les entrées hosts
  - vérifier que les ports 80 et 443 sont libres

- Erreur CORS:
  - vérifier que CORS_ORIGINS est exactement l'URL de l'app dans .env
  - vérifier l'URL utilisée côté navigateur

- Pas de propositions:
  - vérifier le fichier [proposals.json](proposals.json)
  - vérifier les logs backend au démarrage (import)

- Erreur migration:
  - vérifier les variables POSTGRES_*
  - vérifier que le service db est healthy
