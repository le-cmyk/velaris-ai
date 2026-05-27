# Railway Deployment (Backend + PostgreSQL + Redis)

## Backend prerequisites

Backend service is expected at:

- Root Directory: `apps/api`
- Start command: `./start.sh`
- Health endpoint: `/health` and `/api/health`

Required backend environment variables:

```env
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
ENVIRONMENT=production
CORS_ORIGINS=
CLIENT_CONFIG_PATH=
```

## Deploy backend from GitHub

1. Go to Railway.
2. Create a new project.
3. Choose **Deploy from GitHub repo**.
4. Select the Velaris AI repository.
5. Set the backend root directory to `apps/api`.
6. Add a PostgreSQL service.
7. Add a Redis service.
8. Copy the Railway PostgreSQL connection string into `DATABASE_URL`.
9. Copy the Railway Redis connection string into `REDIS_URL`.
10. Add:

```env
JWT_SECRET=change-this-to-a-long-random-secret
ENVIRONMENT=production
CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app
CLIENT_CONFIG_PATH=client-config.example.yaml
```

11. Deploy backend.
12. Open the Railway backend URL.
13. Test:

- `/api/health`
- `/health`

## Initialize database safely

Run in Railway service shell (or Codespaces with the same env vars):

```bash
cd apps/api
python scripts/init_db.py --force
python scripts/seed_demo_user.py --force
```

If you do not pass `--force`, scripts stop when target records already exist.

## Notes

- Keep `CORS_ORIGINS` set to your Vercel frontend domain.
- Do not commit real secrets; use Railway environment variables.
