import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api.v1.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("floodguard_ai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🌊 FloodGuard AI Backend Server Started")
    logger.info(f"🚀 Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")
    logger.info(f"📡 API Prefix: {settings.API_V1_PREFIX}")
    logger.info("💡 Swagger Interactive Docs available at /docs")
    yield
    logger.info("🛑 FloodGuard AI Backend Server Shutting Down")

app = FastAPI(
    title="FloodGuard AI — Hyperlocal Flood Prediction & Safe Routing Platform",
    description=(
        "Production-grade backend engine powering AI flood risk classification, "
        "time-series water level forecasting, multi-factor safe routing, "
        "IoT ESP32 telemetry streaming, and digital flood twin simulation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "tagline": "AI-Powered Hyperlocal Flood Prediction, Drainage Intelligence & Emergency Routing",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
