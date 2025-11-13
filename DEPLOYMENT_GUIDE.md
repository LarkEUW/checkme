# Guide de Déploiement – CheckMe Security Analyzer

Ce document décrit les étapes nécessaires pour exécuter CheckMe en environnement de développement et donne les points d’attention avant toute mise en production. Le dépôt contient plusieurs scripts et fichiers Docker, mais certaines pièces manquent actuellement. Les sections ci-dessous indiquent les actions à réaliser pour un déploiement fonctionnel.

---

## 1. Prérequis

- **Système** : Linux ou macOS (Windows WSL2 recommandé)
- **Backend** : Python 3.11+, `pip`, `virtualenv`
- **Frontend** : Node.js 18 LTS + npm
- **Base de données** : PostgreSQL 15 (locale ou conteneur)
- **Optionnel** : Redis 7 (pour Celery si vous implémentez les tâches asynchrones)
- **Outils** : Git, cURL

---

## 2. Récupération du projet

```bash
git clone <url-du-repo>
cd checkme-platform
```

---

## 3. Préparer la configuration Backend

1. **Créer un environnement virtuel**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Créer `backend/.env`**

   Le dépôt ne fournit pas de fichier `.env.example`. Créez-le manuellement :
   ```env
   # backend/.env
   DATABASE_URL=postgresql+asyncpg://checkme:checkme_password@localhost:5432/checkme_db
   SECRET_KEY=change-me-en-production
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   # Clés externes optionnelles
   # OPENAI_API_KEY=
   # VIRUSTOTAL_API_KEY=
   # ABUSEIPDB_API_KEY=
   ```

3. **Créer `backend/requirements.txt`**

   Le Dockerfile backend suppose l’existence de ce fichier. Ajoutez au minimum :
   ```text
   fastapi
   uvicorn[standard]
   sqlalchemy[asyncio]
   asyncpg
   python-jose[cryptography]
   passlib[bcrypt]
   python-multipart
   aiohttp
   httpx
   ```
   Ajustez selon vos besoins (ex. `alembic`, `celery`, etc.).

4. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

---

## 4. Initialiser PostgreSQL

1. Créez une base et un utilisateur compatibles avec la chaîne de connexion définie plus haut :
   ```sql
   CREATE DATABASE checkme_db;
   CREATE USER checkme WITH PASSWORD 'checkme_password';
   GRANT ALL PRIVILEGES ON DATABASE checkme_db TO checkme;
   ```
2. Assurez-vous que PostgreSQL accepte les connexions depuis le backend (localhost par défaut).

> 💡 Les tables sont créées automatiquement au démarrage via `create_tables()` dans `backend/database.py`.

---

## 5. Lancer l’API FastAPI

Depuis `backend` :

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints utiles :
- `GET /` : ping rapide
- `GET /health` : état de l’application
- `GET /docs` : documentation OpenAPI

---

## 6. Préparer et lancer le Frontend

1. Aller dans le projet Vite :
   ```bash
   cd ../frontend/checkme-frontend
   ```

2. Créer un fichier d’environnement (ex. `.env.local`) :
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. Installer les dépendances et démarrer le serveur Vite :
   ```bash
   npm install
   npm run dev
   ```

4. Accéder à l’interface : <http://localhost:5173>

---

## 7. Authentification et Jeu de Données

Aucun utilisateur par défaut n’est créé dans la base. Utilisez l’endpoint `/api/auth/register` pour enregistrer un compte, puis mettez à jour sa colonne `role` avec `admin` directement dans PostgreSQL si nécessaire.

---

## 8. Utilisation des fichiers Docker

Les fichiers fournis demandent plusieurs ajustements avant de fonctionner :

- `backend/Dockerfile` requiert `backend/requirements.txt` (voir §3).
- `frontend/Dockerfile` suppose que `package.json` se trouve directement dans `frontend/`. Adaptez-le ou déplacez le code (ex. changer `COPY package*.json ./` en `COPY checkme-frontend/package*.json ./` et ajuster les chemins).
- `docker-compose.yml` lance un worker Celery avec `celery -A tasks worker` alors qu’aucun module `tasks` n’existe. Désactivez ce service ou ajoutez l’implémentation manquante.
- `docker-compose.prod.yml` référence `nginx.conf` et `init-db.sql` absents ; créez ces fichiers ou retirez les montages.

Tant que ces éléments ne sont pas fournis, le stack Docker complet ne démarrera pas correctement.

---

## 9. Vérifications Après Déploiement

1. **API** : `curl http://localhost:8000/health` doit renvoyer `{ "status": "healthy", "version": "1.0.0" }`.
2. **Frontend** : vérifiez la connexion API (onglet réseau du navigateur).
3. **Base de données** : confirmez la création des tables (`\dt` dans `psql`).
4. **Fichiers temporaires** : le backend crée `uploads/` et `analysis_workspace/` lors des analyses ; prévoyez un nettoyage périodique.

---

## 10. Points à Surveiller avant Production

- Remplacer toutes les valeurs par défaut (`SECRET_KEY`, mots de passe PostgreSQL, etc.).
- Ajouter une vraie implémentation Celery ou retirer les références.
- Mettre en place Redis si vous activez les tâches asynchrones.
- Prévoir un reverse proxy (ex. Nginx) et des certificats TLS valides.
- Ajouter de la journalisation et de la supervision (ex. Prometheus, Grafana).
- Durcir les contrôles d’accès (rôles, exposition des endpoints d’administration).

---

## 11. Résumé des Écueils Actuels

- Absence de `backend/requirements.txt`.
- Absence de fichiers `.env.example`.
- Docker Compose de production fait référence à des fichiers inexistants (`nginx.conf`, `init-db.sql`).
- Service Celery inexploitable faute de module `tasks`.
- Guide `README-DEPLOYMENT.md` et scripts `deploy*.sh` supposent des ressources non fournies.

Corrigez ces points avant toute automatisation ou déploiement CI/CD.

---

En suivant ce guide et en comblant les lacunes mentionnées, vous pouvez exécuter CheckMe en local et préparer un déploiement plus robuste. N’hésitez pas à enrichir la documentation une fois les éléments manquants ajoutés.
