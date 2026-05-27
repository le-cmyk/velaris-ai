# Vercel Deployment (Frontend)

## Frontend prerequisites

- Root Directory: `apps/web`
- Framework: Next.js
- Required environment variable:

```env
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-BACKEND.up.railway.app
```

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
9. Test login.
10. Test chat.
11. Test approval flow.
12. Test audit logs.

## Notes

- For monorepos, Vercel must point to `apps/web` as root.
- Ensure `CORS_ORIGINS` in Railway includes the Vercel domain.
