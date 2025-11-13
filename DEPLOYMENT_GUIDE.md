# Guide de déploiement CheckMe

## Vue d’ensemble
CheckMe est composé d’un backend FastAPI (Python 3.11+), d’un frontend React/Vite et d’une base PostgreSQL. Le projet propose des fichiers `docker-compose*.yml`, mais certaines pièces doivent encore être ajustées avant d’automatiser complètement le déploiement. Ce guide décrit les prérequis, la configuration des variables et les scenarios de lancement en local ou via Docker Compose.

---

## 1. Prérequis
- Python 3.11 (avec `venv`)
- Node.js 18.x et npm
- PostgreSQL 15 (local ou conteneur)
- Docker ≥ 24 et Docker Compose v2 (pour l’option conteneurisée)
- Accès aux API externes (VirusTotal, OpenAI…) si vous activez ces intégrations

---

## 2. Variables d’environnement essentielles
| Variable | Exemple | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://checkme:checkme_password@localhost:5432/checkme_db` | Chaîne SQLAlchemy async pour PostgreSQL |
| `SECRET_KEY` | `change-me` | Clé utilisée pour signer les JWT (obligatoire en production) |
| `CORS_ORIGINS` | `http://localhost:3000` | Liste séparée par des virgules des origines autorisées |
| `OPENAI_API_KEY` | (optionnel) | Clé si l’analyse IA est activée |
| `VIRUSTOTAL_API_KEY` | (optionnel) | Clé VirusTotal pour l’enrichissement TI |

Créez un fichier `backend/.env` si vous souhaitez centraliser ces valeurs, puis chargez-le via votre shell ou un gestionnaire type `dotenv`.

---

## 3. Mise en route locale (sans Docker)

### 3.1 Base de données PostgreSQL
Lancez une instance locale (ou via Docker) :
```bash
docker run --name checkme-postgres -e POSTGRES_DB=checkme_db \
  -e POSTGRES_USER=checkme -e POSTGRES_PASSWORD=checkme_password \
  -p 5432:5432 -d postgres:15
```

### 3.2 Backend FastAPI
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate

# Installez les dépendances requises (à défaut de requirements.txt)
pip install fastapi uvicorn[standard] sqlalchemy asyncpg \
  passlib[bcrypt] python-jose[cryptography] pydantic python-multipart \
  aiohttp httpx

export DATABASE_URL="postgresql+asyncpg://checkme:checkme_password@localhost:5432/checkme_db"
export SECRET_KEY="change-me-en-production"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.3 Frontend Vite
```bash
cd frontend/checkme-frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev   # ou définissez la variable dans un fichier .env.local
```

Application accessible sur `http://localhost:5173`, API sur `http://localhost:8000`.

---

## 4. Déploiement via Docker Compose

### 4.1 Points à corriger avant le build
1. **`backend/requirements.txt` manquant**  
   Le `Dockerfile` backend copie ce fichier puis lance `pip install -r requirements.txt`. Créez-le avant le build (par ex. en listant les bibliothèques installées localement).

2. **`frontend/Dockerfile`**  
   Le code Vue/React est dans `frontend/checkme-frontend/`. Adaptez le `Dockerfile` (ou déplacez `package.json`) pour que la copie des fichiers fonctionne :
   ```dockerfile
   COPY checkme-frontend/package*.json ./
   COPY checkme-frontend ./
   ```

3. **Service Celery**  
   Les Compose files lancent `celery -A tasks worker`, mais le module `tasks` n’existe pas dans `backend/`. Soit créez ce module avant de lancer le worker, soit commentez temporairement le service `celery`.

4. **Script `deploy.sh`**  
   Il attend `backend/.env.example` et `frontend/.env.example` qui ne sont pas fournis. Créez vos propres fichiers modèle ou exportez les variables manuellement.

### 4.2 Lancement
```bash
# À la racine du projet
docker-compose up -d --build

# Si vous avez préparé la variante prod (avec proxy nginx)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 4.3 Tests rapides
- Backend : `curl http://localhost:8000/health`
- Frontend : `http://localhost:3000`
- Postgres : `docker exec -it checkme-postgres psql -U checkme -d checkme_db`

---

## 5. Durcissement pour la production
- Remplacez tous les mots de passe/secrets par des valeurs fortes.
- Forcez HTTPS via un reverse proxy (NGINX est prévu dans `docker-compose.prod.yml`).
- Activez la journalisation persistante (`./logs`).
- Configurez les sauvegardes PostgreSQL (ex : `pg_dump` via `cron` ou un job Kubernetes).
- Ajoutez de la supervision (ex : Loki + Promtail pour les logs, Grafana/Prometheus pour les métriques).

---

## 6. Dépannage courant
- **Le backend échoue au démarrage** : vérifier `DATABASE_URL`, la connectivité PostgreSQL et l’existence des tables (`create_tables()` est exécuté au lancement).
- **Le build Docker échoue** : s’assurer que les points listés en 4.1 sont résolus.
- **Front-end n’arrive pas à joindre l’API** : vérifier la variable `VITE_API_URL` et les règles CORS (`CORS_ORIGINS` côté backend).
- **Analyse en échec immédiat** : consulter les logs du backend (`docker-compose logs backend`) ; l’analyse échoue actuellement si les métadonnées magasin contiennent une date (cf. section revue de code).

---

## 7. Étapes suivantes suggérées
- Versionner les fichiers `requirements.txt` (backend) et `.env.example`.
- Corriger ou retirer le service Celery tant que le module `tasks` n’existe pas.
- Mettre en place un pipeline CI/CD (lint/tests → build images → déploiement).
- Compléter la documentation API et la procédure de provisioning (utilisateurs, rôles, clés API externes).

Ce guide sera à mettre à jour une fois les ajustements ci-dessus intégrés au dépôt.
