# SafeHer AI

SafeHer AI is a women’s safety and rights assistance application. It offers supportive, general guidance and links to reviewed rights information. It is not an emergency service or a substitute for legal advice. The app does not claim to contact or dispatch responders. Emergency and nearby support records remain empty until an administrator adds verified, region-specific resources.

## Main features

- Responsive Home, AI Assistant, Emergency Help, Know Your Rights, Complaint Guidance, Nearby Help, and privacy pages.
- English, Hindi, and Hinglish-friendly chat with follow-up questions and emergency cue handling.
- TF-IDF and Logistic Regression complaint-category classifier.
- Retrieval from a structured rights knowledge base with official-source references.
- Optional browser speech input/output and opt-in browser location for nearby resource search.
- FastAPI endpoints for chat, classification, rights retrieval, nearby help, complaint guidance, health, categories, and protected resource administration.
- Optional MongoDB storage for reviewed support resources, emergency contacts, rights records, and complaint categories. Chat text, complaint narratives, user profiles, and location history are not stored by the app.

## Technology and structure

- **Frontend:** static HTML, CSS, and vanilla JavaScript in `frontend/`. It is not React and does not use npm or a frontend bundler.
- **Backend:** Python FastAPI with Uvicorn in `backend/`.
- **ML:** scikit-learn TF-IDF plus Logistic Regression and its saved model in `ml/`.
- **AI agent and rights retrieval:** Python modules and reviewed JSON records in `ai_agent/`.
- **Database:** MongoDB is optional for local development; configure MongoDB Atlas or another reachable MongoDB deployment for durable hosted data.

## Local setup (Windows PowerShell)

Run these commands from the `outputs/` directory. Python and Node.js are needed for setup; Node.js is used only to generate the frontend’s runtime API configuration.

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m ml.train_model
node frontend\build-config.mjs
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal, also from `outputs/`, serve the static frontend:

```powershell
python -m http.server 5500
```

Open `http://localhost:5500`. FastAPI’s interactive API documentation is at `http://127.0.0.1:8000/docs`. The frontend requests location only after the user chooses the nearby-help action. Speech recognition and synthesis depend on browser support and permissions.

## Environment variables

The backend loads optional local settings from `backend/.env`. Start from the variable-name-only template:

```powershell
Copy-Item backend\.env.example backend\.env
```

Leave unused values blank. Important settings include:

- `FRONTEND_ORIGINS`: exact comma-separated frontend origins; do not use `*`.
- `MONGODB_URI` and `MONGODB_DATABASE`: enable MongoDB persistence.
- `AI_PROVIDER`: defaults to `demo`; only use `remote_json` with a verified compatible provider.
- `AI_API_URL`, `AI_API_KEY`, and `AI_MODEL_NAME`: backend-only settings for that optional remote provider.
- `ADMIN_API_KEY`: optional strong key for protected `/admin` resource-management endpoints.
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: optional per-process rate limit.

Never commit a real `.env` or put a database credential, AI key, or admin key in frontend code. The frontend’s `SAFEHER_PUBLIC_API_URL` is a public HTTPS backend origin, not a secret. On a hosting provider, set it in the **frontend build environment**; the production config generator validates it and writes `frontend/runtime-config.js`:

```sh
node frontend/build-config.mjs --production
```

## Deployment architecture

Recommended deployment uses a Render Static Site for `frontend/` and the root redirect, a Render Python Web Service for FastAPI, and MongoDB Atlas for durable database storage. Configure `SAFEHER_PUBLIC_API_URL` on the static site and set `FRONTEND_ORIGINS` on the API to the exact deployed frontend origin. Store `MONGODB_URI`, `ADMIN_API_KEY`, and any optional `AI_API_KEY` only in backend-hosting secret settings. See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for repository, build/start commands, environment setup, database networking, and post-deployment verification steps.
