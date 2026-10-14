# SafeHer AI — production deployment guide

## Audit summary

- **Frontend:** static HTML, CSS, and browser JavaScript in `frontend/`; no React, npm, package manager, or bundler.
- **Backend:** Python FastAPI in `backend/`, served by Uvicorn.
- **Database:** MongoDB support exists but is optional. No production URI is configured; without it the API uses local JSON files, which are not durable on hosted containers.
- **ML and agent:** the classifier, model artifact, AI agent, and reviewed rights records are local project files loaded by the backend. The default agent provider is the no-secret `demo` adapter.
- **Routes:** `POST /chat`, `POST /classify`, `GET /rights`, `POST /nearby-help` (plus legacy GET), `POST /complaint`, `GET /complaint-categories`, `GET /health`, FastAPI `/docs` and `/openapi.json`; protected registry CRUD is under `/admin`.
- **Existing deployment/build setup:** no Git remote, Dockerfile, Render/Vercel/Railway manifest, frontend package manager, or production build was present. `outputs/` is the deployable project directory.

## Production config added

The static frontend cannot read private server environment variables in the browser. Its build now reads the **public API origin** from `SAFEHER_PUBLIC_API_URL` and writes it to `frontend/runtime-config.js`. That value is a public URL, not a secret. Production builds require HTTPS and reject credentials, paths, query strings, and fragments. Local development continues to use `http://127.0.0.1:8000` only on localhost.

The backend reads configuration from environment variables. `backend/.env.example` contains variable names with blank values only. The project-level `.gitignore` excludes real `.env` files and local Python/cache files. Never put `MONGODB_URI`, `ADMIN_API_KEY`, or `AI_API_KEY` in frontend files or in `SAFEHER_PUBLIC_API_URL`.

There is no browser bundle step. The frontend production build/check is:

```sh
node frontend/build-config.mjs --production
```

It needs `SAFEHER_PUBLIC_API_URL` set in the frontend hosting environment. A missing or non-HTTPS value is a build error. Local config generation (without requiring an API URL) is `node frontend/build-config.mjs`.

## Recommended hosting

Use **Render** for one static site and one Python web service, and **MongoDB Atlas** for the managed MongoDB database. This matches the existing separate static frontend/FastAPI architecture and avoids adding Docker, a frontend framework, or a new database. Official setup references: [Render FastAPI deployment](https://render.com/docs/deploy-fastapi), [Render static sites](https://render.com/docs/static-sites), [Render environment variables](https://render.com/docs/configure-environment-variables), and [MongoDB Atlas connection](https://www.mongodb.com/docs/atlas/connect-to-database-deployment/).

## Manual deployment steps

No GitHub remote, hosting account, or deployment credentials are configured in this workspace, so a live deployment cannot be performed here. A local Git repository is now initialized in `outputs/`. First create an empty private repository on [GitHub](https://github.com/signup). From PowerShell, run these commands in the `outputs` directory, replacing the remote URL with the URL GitHub gives you:

```powershell
git add .
git status
git commit -m "Prepare SafeHer AI for deployment"
git branch -M main
git remote add origin <your-private-repository-url>
git push -u origin main
```

Review `git status` before committing. `.env` files must not appear in the staged files. Do not create a real `.env` in this repository.

### 1. Create the database

1. Create a MongoDB Atlas account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) and create a cluster.
2. Create a **database user** for the app with only the required database privileges; the Atlas website login is a different account.
3. In Atlas Network Access, allow only the app host's documented outbound IP range or use its private networking option. Do not allow all IPs. Atlas requires the app host's outbound address to be on the access list.
4. Copy the driver connection string from Atlas. Keep it private; do not paste it in chat, source files, or frontend settings. Replace any Atlas placeholders in the dashboard only.

### 2. Deploy the FastAPI backend on Render

1. Create a [Render account](https://dashboard.render.com/register), choose **New → Web Service**, and connect the GitHub repository.
2. Leave **Root Directory** blank so Render uses the repository root (the repository root is the contents of `outputs/`).
3. Set **Language** to Python 3, **Build Command** to:

   ```sh
   pip install -r backend/requirements.txt
   ```

   Set **Start Command** to:

   ```sh
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```

4. In that web service's **Environment** page add:

   | Variable | Value to enter |
   | --- | --- |
   | `FRONTEND_ORIGINS` | Temporarily leave the existing default during the first backend deploy. Replace it with the exact static-site origin after creating the frontend, e.g. the origin Render assigned, with no trailing slash. |
   | `MONGODB_URI` | The private Atlas driver connection string. |
   | `MONGODB_DATABASE` | The chosen database name; `safeher_ai` is the app's default if omitted. |
   | `AI_PROVIDER` | `demo` (does not need an AI key). |
   | `RATE_LIMIT_REQUESTS_PER_MINUTE` | Optional; set only if you want to override the default. |
   | `ADMIN_API_KEY` | Optional, only if you need the protected `/admin` registry endpoints. Generate a unique random value of at least 32 characters in a password manager. |

   Add optional `AI_API_URL`, `AI_API_KEY`, and `AI_MODEL_NAME` **only** when you have a verified compatible remote model gateway. Do not enable remote mode with demo/test credentials. Keep `ADMIN_API_KEY`, `MONGODB_URI`, and `AI_API_KEY` in the backend service's secret environment settings only. Do not add the file paths from `.env.example`; the existing defaults point to the bundled project files.

5. Deploy. Copy the public backend origin (the `https://...onrender.com` base address) from the Render dashboard. Verify `https://<backend-origin>/health` returns JSON. The health endpoint reports whether MongoDB is connected; it must report `mongodb` for durable production registry data.

### 3. Deploy the static frontend on Render

1. Choose **New → Static Site**, select the same GitHub repository, and leave **Root Directory** blank so Render uses the repository root (the repository root is the contents of `outputs/`).
2. Use this **Build Command**:

   ```sh
   node frontend/build-config.mjs --production
   ```

   Set **Publish Directory** to `.`.
3. In the static site's **Environment** settings, add `SAFEHER_PUBLIC_API_URL` with the backend's HTTPS origin from the prior step (origin only; no `/chat` path). This is public configuration and contains no credential.
4. Deploy. Copy the frontend's assigned HTTPS origin. In the backend service's Environment settings, set `FRONTEND_ORIGINS` to this **exact origin**. Save and redeploy the backend so CORS permits this site only.
5. If using a custom domain, add its exact HTTPS origin to `FRONTEND_ORIGINS` and redeploy; add it to the static site's domain settings too.

### 4. Final live verification

After both services are deployed and CORS is updated:

1. Open the frontend's HTTPS URL. Check Home and each navigation page; refresh on `/#assistant` and `/#rights` to verify the static route still loads.
2. In the browser, send a harmless demo chat prompt and check the response. Test `GET <backend-origin>/health`, `/docs`, `/complaint-categories`, `/rights`, and submit valid and invalid requests in `/docs` for `/chat`, `/classify`, `/complaint`, and `/nearby-help`.
3. Confirm an allowed frontend request succeeds and an unrelated origin is denied by CORS. Check browser devtools for failed requests, mixed-content warnings, and console errors.
4. Confirm `/health` reports `mongodb`; verify expected curated records and indexes through the protected admin/API path if configured. Do not enter real personal narratives or real location data during smoke tests.
5. Check mobile layout in browser device emulation. Verify the emergency screen does not imply SafeHer can call or dispatch services. The bundled support and emergency lists are intentionally empty until verified local resources are configured; do not expect nearby contacts until that is done.

The final live URL and live-test result are unknown until the hosting accounts, repository, database, and deployments are created. Do not mark deployment complete before these checks pass.
