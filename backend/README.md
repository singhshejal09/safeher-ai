# SafeHer AI FastAPI backend

The app uses small layers so each part has one job:

- `app/main.py` creates FastAPI, the CORS policy, health route, and OpenAPI docs.
- `app/api/routes/` defines one HTTP route module per feature.
- `app/schemas/requests.py` validates request bodies and location coordinates.
- `app/services/` connects routes to ML, reviewed rights records, nearby resources, and complaint guidance.
- `app/db/mongodb.py` owns the MongoDB connection and database CRUD helpers; business services call it instead of talking to MongoDB directly.
- `config/support_resources.json` is the backend-owned registry for verified support services and emergency contacts.
- `../ml/` contains the TF-IDF + Logistic Regression dataset, training script, and model artifact.
- `../ai_agent/` contains chat orchestration, safety rules, verified rights lookup, and swappable model adapters.
- `../ai_agent/data/rights_knowledge.json` is the reviewed, India-scoped multilingual rights/support seed corpus.

## Run locally (Windows PowerShell)

From the `outputs/` directory, create an environment and install dependencies:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m ml.train_model
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal from `outputs/`, serve the frontend:

```powershell
python -m http.server 5500
```

Open `http://localhost:5500`. Interactive API docs are at `http://127.0.0.1:8000/docs`; the generated OpenAPI schema is at `/openapi.json`.

## MongoDB

MongoDB is optional for the existing local demo. With `MONGODB_URI` empty, the backend keeps using the JSON files and does not connect to a database. To enable MongoDB, install dependencies as above and set `MONGODB_URI` and `MONGODB_DATABASE` in `backend/.env` (copy `.env.example` first). Keep credentials out of source control. On startup the API pings MongoDB, creates unique `id` indexes, and inserts baseline complaint categories if missing. If a configured database cannot connect, startup fails rather than silently switching data stores.

The database uses four collections:

| Collection | Contents |
| --- | --- |
| `support_services` | Verified local support services, source, jurisdiction, review date, and map coordinates |
| `emergency_contacts` | Configurable official contacts, coverage area, and source metadata |
| `rights_knowledge` | Rights summaries tied to jurisdiction and official source citations |
| `complaint_categories` | Category identifiers, display labels, descriptions, and active status |

No chat history, complaint narrative, user profile, or location lookup history is written to MongoDB. Coordinates are used only for the nearby-help response. Category documents are metadata; changing a label does not retrain the separate ML model or change its trained category labels.

### Registry CRUD

Set a randomly generated `ADMIN_API_KEY` of at least 32 characters in `backend/.env` before managing records. Admin requests use constant-time key comparison; admin CRUD is disabled without the key and MongoDB. Use HTTPS outside local development. `/admin/{registry}` routes require it in the `X-Admin-Key` header and are disabled if the key is unset. Supported names: `support-services`, `emergency-contacts`, `rights`, `complaint-categories`.

- `GET /admin/{registry}` and `GET /admin/{registry}/{id}` read records.
- `POST /admin/{registry}` creates a record with a generated ID.
- `PUT /admin/{registry}/{id}` replaces or creates a record with that ID.
- `DELETE /admin/{registry}/{id}` removes a record.

Use FastAPI docs to select a route, add the admin header, and submit a JSON record. Pydantic validates fields and coordinates; source records require HTTPS URLs and valid review dates. New source entries default to `pending`; only complete records marked `verified` are shown by public rights/nearby endpoints. Invalid payloads return `422`; database failures return a generic `503`.

## Endpoints

- `POST /chat` accepts `{"message":"...","history":[],"jurisdiction":null}`. The agent classifies the message, checks emergency cues, asks a relevant follow-up, and returns reviewed rights citations only when jurisdiction-specific sources are verified.
- `POST /classify` accepts `{"text":"..."}` and returns category, confidence, category scores, model version, and `needs_clarification` when confidence is below the baseline threshold. Confidence is not a calibrated probability; low-confidence labels should not be treated as facts.
- `GET /rights?category=...&jurisdiction=...` returns only current entries marked verified with HTTPS sources and review metadata. Without matching data, the list is empty.
- `GET /rights?query=...&jurisdiction=India&language=hi` ranks matching entries from the reviewed knowledge base and returns the requested language.
- `GET /complaint-categories` lists the complaint classifier categories.
- `POST /nearby-help` accepts coordinates in a validated JSON body and returns distance-sorted verified services and coverage-matched emergency contacts. The frontend calls it only after browser geolocation permission is granted. A legacy GET route remains for compatibility; avoid it in production because URL query strings can appear in access logs.
- `POST /complaint` accepts `{"text":"...","preferred_language":"en"}` and returns a category plus general organizing steps. Text is not saved; emergency predictions receive safety guidance.
- `GET /health` is a simple status route.

Pydantic validates and normalizes user text, rejects unexpected fields, bounds request/history/coordinate values, and limits chat history to user/assistant roles. Structured `422` errors omit submitted values. API exceptions return generic messages without internal tracebacks. A short in-memory per-process rate limit (default 60 requests/minute/client/endpoint) protects chat, classification, complaint, rights retrieval, location, and admin routes and returns `429` with `Retry-After`. For multi-worker/production deployments, enforce shared rate limits at a trusted gateway too. Responses include security headers; user-sensitive API responses are marked `no-store`.

## Rights RAG flow

For a rights-related chat, the request includes a country/region. The agent passes the question, detected language, and classifier category to `app/services/rights.py`. `ai_agent/knowledge_base.py` filters out non-verified, stale, mismatched-jurisdiction, or non-official-host records, then ranks the remaining passages using multilingual keywords and text overlap. The agent answers from the retrieved passage and returns its title, topic, source name, review date, and official URL as citations. The legal branch does not ask the model provider to invent or expand law. If jurisdiction is missing or no relevant source is retrieved, it says it cannot verify the legal answer. This is a simple retrieval-augmented generation (RAG) pattern; the user-facing response is assembled from reviewed content rather than free-form legal generation.

The bundled entries cover domestic-violence protections, stalking/sexual-harassment statute references, workplace sexual harassment, free legal-aid information, Women Helpline 181, the national cybercrime portal, and SHe-Box. Records are excluded when their review is more than one year old. These records are scoped to India; Hindi or Hinglish does not automatically set the jurisdiction. The chat and rights pages ask the user to explicitly choose India first.

## Configuration

Copy `.env.example` to `.env` for local overrides. `FRONTEND_ORIGINS` is the comma-separated exact CORS allowlist; wildcard origins are rejected. `RATE_LIMIT_REQUESTS_PER_MINUTE` defaults to 60 per client and endpoint. `AI_PROVIDER=demo` works without secrets. For a model gateway, select `remote_json` and set `AI_API_URL`, `AI_API_KEY`, and `AI_MODEL_NAME`. Set `MONGODB_URI`, `MONGODB_DATABASE`, and `ADMIN_API_KEY` to enable the database and protected CRUD. The gateway contract is documented in `../ai_agent/model_provider.py`. `.env` and virtual environments are ignored by Git.

The support and emergency-contact registries intentionally start empty. The rights JSON corpus contains a small India-scoped seed set. Add only reviewed records with source, jurisdiction/coverage, HTTPS official source URL, and review date. No legal conclusions or unverified emergency numbers are fabricated. SafeHer AI is guidance software; it is not legal counsel and does not contact or dispatch emergency services.


## Security and privacy notes

- Keep .env out of source control. Frontend resources.js contains only public settings; never put AI, MongoDB, or admin credentials there. Remote AI endpoints must use HTTPS (HTTP is accepted only for localhost), and redirects are refused so messages and the API key stay with the configured host.
- CORS permits only explicit origins from FRONTEND_ORIGINS; wildcard origins are rejected. No cookie credentials are enabled.
- No user accounts or protected user data exist, so public guidance/lookup routes do not require user authentication. MongoDB registry CRUD is an administrative function protected by the strong X-Admin-Key; deploy it over HTTPS and rotate the key if exposed.
- User messages and complaint text are not stored by SafeHer. A configured external model provider receives the current message and recent validated history. Avoid entering identifying information. Browser speech recognition may process audio through the browser's configured service; SafeHer stores no audio.
- Geolocation is requested only after the user presses the nearby-help button and approves the browser prompt. The frontend sends coordinates in the POST body (not the URL) and the backend does not persist them. The mapping tile provider can observe map requests after the user opts in. Legacy GET lookup remains only for compatibility.
- Local rate limiting stores only a short-lived in-memory timestamp window associated with client address and endpoint; it is not written to MongoDB. It is process-local, so production should add gateway-level shared throttling.
- Emergency/support contacts remain administrator-configured and require source/review metadata before display. The application clearly labels AI guidance separately; it cannot contact responders or provide legal advice.
