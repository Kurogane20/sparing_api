# SPARING API (FastAPI + MySQL)

Production-grade API for wastewater monitoring.

## Quickstart (Docker)

```bash
cp .env.example .env
docker compose up --build
# (first boot runs Alembic and serves at http://localhost:8000)
```

Run seed:
```bash
docker compose exec api bash -lc "python seed.py"
```

Open docs: http://localhost:8000/docs

Default users (after seed):
- admin@example.com / Admin#123 (admin)
- op@example.com / Op#12345 (operator)
- viewer@example.com / Viewer#123 (viewer, bound to site `aqmsFOEmmEPISI01` only)

## Key Endpoints

- `POST /auth/login`
- `GET /me`
- `POST /auth/register` (admin)
- `POST /auth/refresh`
- `POST /auth/logout`

- `POST /sites` (admin/operator)
- `GET /sites`
- `GET /sites/{id}`
- `PATCH /sites/{id}`
- `DELETE /sites/{id}` (admin)

- `POST /devices` (admin/operator)
- `GET /devices?site_uid=...`
- `GET /devices/{id}`
- `PATCH /devices/{id}`
- `DELETE /devices/{id}` (admin)

- `POST /ingest/state` (+ optional `Idempotency-Key` header)
- `POST /ingest/bulk`

- `GET /data?site_uid=...&date_from=...&date_to=...&page=1&per_page=50&order=desc&fields=ph,tss,debit`
- `GET /data/last?site_uid=...`

- `GET /sites/{uid}/stats/last-seen`
- `GET /sites/{uid}/metrics`

## Notes

- UTC is stored in DB; timestamps accepted with any offset and normalized to UTC.
- Viewer scoping enforced: viewers can **only** read sites assigned to them; they cannot POST/PATCH/DELETE.
- Simple in-memory rate limit for `/ingest/*` (configure via `RATE_LIMIT_PER_MIN`).
- JSON structured logging with request IDs.
- Alembic migration creates all tables & indexes.
- Use `GUNICORN_WORKERS` to scale. For multi-instance rate limiting, replace middleware with Redis-based limiter.
- Add S3 export / webhook / MQTT bridge as needed in `services/`.
