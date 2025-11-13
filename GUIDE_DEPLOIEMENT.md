# Guide de déploiement – CheckMe

Ce document décrit la procédure recommandée pour mettre en ligne la plateforme **CheckMe** (FastAPI + React) dans l’état actuel du dépôt. Il met aussi en évidence les points bloquants observés durant l’audit afin de garantir un déploiement reproductible.

---

## 1. Vue d’ensemble

- **Backend** : FastAPI (Python 3.11+), PostgreSQL, tâches asynchrones pour l’analyse.
- **Frontend** : Vite + React 18, communication via `/api`.
- **Conteneurisation** : Docker Compose (développement) + fichier `docker-compose.prod.yml` pour une cible plus réaliste.
- **Services additionnels** : Redis et un worker Celery sont référencés mais absents du code (pas de module `tasks`).

---

## 2. Pré‑requis

| Usage | Pré‑requis |
|-------|------------|
| Développement local (sans Docker) | Python 3.11+, Node.js 18+, PostgreSQL 15+, Redis (optionnel) |
| Développement via Docker Compose | Docker >= 24, Docker Compose >= 2.20 |
| Production | Accès à un registre de conteneurs, solution SSL/TLS (nginx/Traefik), système de logs & sauvegardes |

---

## 3. Points bloquants à corriger avant tout déploiement

1. **Fichier `backend/requirements.txt` absent**  
   Le `Dockerfile` backend l’attend. Créez le fichier avec au minimum :
   ```text
   fastapi==0.111.1
   uvicorn[standard]==0.30.1
   sqlalchemy[asyncio]==2.0.35
   asyncpg==0.30.0
   alembic==1.13.2
   python-jose[cryptography]==3.4.0
   passlib[bcrypt]==1.7.4
   python-multipart==0.0.9
   aiohttp==3.10.5
   httpx==0.27.2
   ```

2. **Pas de fichiers d’exemple `.env`**  
   Les scripts (`deploy.sh`, `README-DEPLOYMENT.md`) supposent `backend/.env.example` et `frontend/.env.example`. Créez-les ou renseignez directement vos variables d’environnement (voir §4.3).

3. **Service Celery inutilisable**  
   - Aucun module `tasks.py`.  
   - Aucune dépendance Celery listée.  
   ➜ Supprimez/ignorez le service `celery` dans les fichiers Compose tant que le worker n’est pas implémenté.

4. **`frontend/Dockerfile` pointe sur le mauvais dossier**  
   La configuration attend `package*.json` dans `frontend/`, alors qu’ils se trouvent dans `frontend/checkme-frontend/`.  
   ➜ Déplacez le `Dockerfile` dans `frontend/checkme-frontend/` **ou** ajustez les instructions de copie (`COPY checkme-frontend/package*.json ./` etc.).

5. **Fichiers référencés mais absents en production**  
   - `docker-compose.prod.yml` attend `nginx.conf`, `ssl/`, `init-db.sql`, `logs/`.  
   ➜ Fournissez ces fichiers avant un déploiement réel ou supprimez les montages correspondants.

6. **Absence d’administrateur initial**  
   Aucune migration ni script de seed ne crée un compte admin. Pensez à insérer manuellement un compte administrateur dans la base avant l’ouverture à vos équipes SOC.

---

## 4. Déploiement sans Docker (mode développeur)

### 4.1 Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # après création du fichier manquant

# Variables nécessaires (exemple)
export DATABASE_URL=postgresql+asyncpg://checkme:checkme_password@localhost:5432/checkme_db
export SECRET_KEY="change-me"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Frontend

```bash
cd frontend/checkme-frontend
npm install
npm run dev
```

Une configuration Vite existe déjà pour proxifier `/api` vers `http://localhost:8000`.

### 4.3 Variables d’environnement minimales

`backend` :
```env
DATABASE_URL=postgresql+asyncpg://checkme:checkme_password@postgres:5432/checkme_db
SECRET_KEY=remplacez_par_un_token_long
OPENAI_API_KEY=...            # optionnel
VIRUSTOTAL_API_KEY=...        # optionnel
```

`frontend` :
```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_AI_ANALYSIS=true
```

---

## 5. Déploiement avec Docker Compose (après corrections)

1. **Préparer les ressources**  
   - Ajouter `backend/requirements.txt`.  
   - Créer `backend/.env`, `frontend/checkme-frontend/.env`.  
   - Ajuster le `Dockerfile` frontend (voir §3.4).  
   - Retirer (ou commenter) le service `celery` si non utilisé.

2. **Démarrer les conteneurs**  
   ```bash
   docker compose up -d --build
   ```

3. **Vérifier les services**  
   - API : `http://localhost:8000/health`  
   - Frontend : `http://localhost:3000` (commandé par Vite en mode dev)  
   - PostgreSQL : `docker compose exec postgres pg_isready -U checkme`

4. **Initialiser un administrateur**  
   Connectez-vous à PostgreSQL et mettez à jour le rôle d’un utilisateur :
   ```sql
   UPDATE users SET role = 'admin' WHERE email = 'mon.admin@example.com';
   ```

---

## 6. Notes pour la production

- **Construit multi-étapes** : remplacez le `npm run dev` par `npm run build` + serveur statique (nginx ou `vite preview`).  
- **Reverse proxy** : fournissez un `nginx.conf` qui :
  - sert le frontend sur `/` ;
  - proxifie `/api` vers le backend FastAPI.
- **Secrets** : stockez `SECRET_KEY`, API keys et mots de passe via votre gestionnaire de secrets (Vault, AWS Parameter Store…).
- **Supervision** : activez les logs d’accès nginx, les métriques FastAPI (`/health`), et sauvegardez la base PostgreSQL (volumes externes + `pg_dump`).
- **Sécurité** : activez HTTPS, changez toutes les valeurs par défaut, configurez le CORS (`CORS_ORIGINS`).

---

## 7. Checklist de validation

- [ ] `backend/requirements.txt` présent et utilisé lors du build.  
- [ ] Fichiers `.env` renseignés et montés dans les conteneurs.  
- [ ] Service `celery` désactivé ou implémenté.  
- [ ] `frontend/Dockerfile` copie bien les bons fichiers.  
- [ ] `nginx.conf`, certificats et scripts d’initialisation fournis pour la prod.  
- [ ] Compte administrateur créé.  
- [ ] Tests manuels :  
  - création d’un utilisateur,  
  - lancement d’une analyse par fichier,  
  - consultation & suppression d’un rapport.

---

## 8. Ressources complémentaires

- Documentation FastAPI : https://fastapi.tiangolo.com/  
- Documentation Vite : https://vitejs.dev/guide/  
- Modèle de configuration nginx + Vite : https://vitejs.dev/guide/static-deploy.html#nginx

---

*Dernière mise à jour : 13 novembre 2025.*
