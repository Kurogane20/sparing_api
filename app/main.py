from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse  # 👈
from app.core.config import settings
from app.api.routers import auth, sites, devices, ingest, data, metrics, admin, getdata
from app.middlewares.request_id import RequestIDMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.core.db import init_models
from app.core.logging import logger

# ✅ pakai JSONResponse sebagai default (atau hilangkan param ini)
app = FastAPI(title="SPARING API", version="1.0.0", default_response_class=JSONResponse)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, routes_prefix=["/ingest"], rate_per_min=settings.rate_limit_per_min)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(sites.router, prefix="/sites", tags=["Sites"])
app.include_router(devices.router, prefix="/devices", tags=["Devices"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(metrics.router, tags=["Metrics"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(getdata.router, tags=["GetData"])

@app.get("/healthz", tags=["Health"])
async def healthz():
    try:
        await init_models()
        return {"ok": True}  # ✅ otomatis jadi JSON
    except Exception:
        logger.exception("Health check failed")
        return JSONResponse({"ok": False}, status_code=500)  # ✅
