# Render live verification — 14 October 2026

- Repository: private `tindepzai12-hash/ui-smart-fcl`, branch `main`.
- Service: https://ui-smart-fcl.onrender.com — Free, Node 24.13.0, Singapore.
- Application commit verified: `6d689986e6b94fd80b4a7ebba443144f85dc015e`.
- Local verification: production frontend build, 30 Python regression tests, 8 frontend tests, 2 Node gateway security tests passed. Node gateway tests also passed during the native Linux Render build.
- Live `tests/cloud-smoke.py`: passed authentication, public health redaction, English/Vietnamese OCR, four-document synthetic FCL processing, preserved invoice leading zeros, Reviewed export rejection, seven-sheet Draft workbook, backup ZIP and all four synthetic demo document endpoints. Only its own synthetic case was removed after testing; customer data was not used or uploaded.
- Browser verification: password login in the Codex browser works; Settings reports backend/SQLite ready and OCR `eng, vie`. The cloud demo storage warning is visible. Login was changed to support embedded browsers while retaining a standard form fallback.
- Runtime OCR libraries are bundled separately because the native runtime image lacks `libarchive.so.13`, despite the build image containing it. The wrapper sets paths only for Tesseract, not the Python processor.
- OpenAI live verification is pending secure key configuration. Previous mocked tests validate the adapter but do not prove an actual OpenAI connection. Do not describe OpenAI as connected until a real probe succeeds.
- Render uses default TCP readiness for this MCP-created service; Node waits for Python/SQLite before binding. See `RENDER_DEPLOY.md` for enabling `/healthz` HTTP health checks in the dashboard.
- This verifies a cloud demo, not production readiness, customer OCR accuracy, ECUS/VNACCS integration, per-user authorization or durable cloud storage.
