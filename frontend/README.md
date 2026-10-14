# SafeHer AI frontend

This is the existing responsive HTML/CSS/JavaScript frontend. It is not a React app and has no npm build step. The `outputs/index.html` entry point redirects here so the earlier app path remains usable.

For local development, serve the parent `outputs/` directory on port 5500 and run the FastAPI service on port 8000. The frontend uses the loopback API only when opened on `localhost` or `127.0.0.1`. For production, set `SAFEHER_PUBLIC_API_URL` in the static host's build environment and run `node frontend/build-config.mjs --production`; this generates the public API origin in `runtime-config.js`. Never put private API, database, or admin credentials in browser code. Geolocation is requested only after the user activates **Find Nearby Help**.