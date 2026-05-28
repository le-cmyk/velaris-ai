# Vercel Deployment (Frontend)

## Frontend prerequisites

- Root Directory: `apps/web`
- Framework: Next.js
- Required environment variable:

```env
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-BACKEND.up.railway.app
```

> **Security reminder:** Only `NEXT_PUBLIC_API_URL` should be added to Vercel. **Never** add `OPENROUTER_API_KEY`, `JWT_SECRET`, `DATABASE_URL`, or any backend secret to Vercel — these must remain on the Railway backend only.

## Deploy frontend from GitHub

1. Go to Vercel.
2. Create a new project.
3. Import the GitHub repository.
4. Set the Root Directory to `apps/web`.
5. Set the framework to Next.js.
6. Add environment variable:

```env
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-BACKEND.up.railway.app
```

7. Deploy.
8. Open the Vercel URL.
9. Test login with demo credentials (`demo@velaris.ai` / `demo123`).
10. Test signup — new account should create a workspace and seed data.
11. Test `/dashboard/data` — seeded records should appear.
12. Test chat — ask "List my customers".
13. Test approval flow.
14. Test audit logs.

## Notes

- For monorepos, Vercel must point to `apps/web` as root.
- Ensure `CORS_ORIGINS` in Railway includes the Vercel domain.
- The LLM key (`OPENROUTER_API_KEY`) is a backend-only variable — setting it on Vercel would expose it publicly via `NEXT_PUBLIC_*` prefixing. Keep it on Railway only.
