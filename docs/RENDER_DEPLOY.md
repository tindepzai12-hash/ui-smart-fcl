# U&I SMART — Render Free / Node

This is a private, shared demo workspace, not a production multi-tenant service.

## Architecture

Native Node gateway (`npm start`) binds `0.0.0.0:$PORT`. It starts the existing Python/FastAPI document processor on loopback only. A password login protects the app, uploads, API, settings, exports and backups. `/healthz` exposes only readiness. Signed HttpOnly/Secure/SameSite=Strict sessions expire after eight hours. Cross-origin writes are rejected; the existing backend mutation-header guard remains active.

This is a Node deployment with a Python document engine, not a rewrite of document parsing into JavaScript. Native Render runtimes include Python. The build extracts Debian Tesseract packages without root, with English and Vietnamese OCR.

## Configuration

- Runtime: Node; region: Singapore; instance: Free; branch: main.
- Build: `bash scripts/render-build.sh`; start: `npm start`; health: `/healthz`.
- Required secret environment values: `UI_SMART_PASSWORD` (16+ characters), `UI_SMART_SESSION_SECRET` (32+ random characters).
- Optional: `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4.1-mini`). Do not commit keys or paste them in chat.
- Node 24; Python 3 from native runtime; Python dependencies installed in ignored `vendor/`.

## Data and access

Render Free loses the SQLite database and uploaded files on sleep, restart or redeploy. The interface and login page explicitly disclose this. Use Settings → Backup before leaving. Do not treat this as the only copy of business records. The local app remains available with its original data. Existing local customer data is never deployed or committed.

The password grants access to the entire shared workspace and OpenAI configuration. Give it only to trusted collaborators. There are no per-user roles or tenant isolation. The login throttles repeated failures globally; this may briefly block all users after ten wrong attempts.

The Free instance sleeps after 15 minutes idle; wake-up is approximately one minute. Usage quotas are shared with other Free services in the Render workspace. No paid database or disk is provisioned by this configuration.

## OpenAI

For a persistent server configuration, enter `OPENAI_API_KEY` in Render → service → Environment, save and redeploy. Then use Settings → Test connection. A real Structured Outputs request checks access without sending customer documents. The page reports "connected" only after this succeeds. OpenAI API usage is billed separately from Render Free.

Alternatively, enter the key in the protected app settings. That key exists only in server memory and must be entered again after sleep/restart. Document processing still requires explicit consent before sending content to OpenAI. Files are treated as untrusted data; employees verify extracted values and evidence before Reviewed exports.

## Verification

Run `node --test tests/cloud-gateway.test.mjs`, the frontend tests/build and the Python regression suite. After deployment verify unauthenticated API denial, login/logout, public health redaction, OCR languages, a synthetic FCL job, backup download and OpenAI status. Never use existing customer records for deployment smoke tests.

Official references: https://render.com/docs/native-runtimes · https://render.com/docs/regions · https://render.com/docs/free
