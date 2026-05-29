import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1_router import router as v1_router
from app.core.database import init_db
from app.worker.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing async database...")
    await init_db()
    
    logger.info("Starting autonomous background scheduler...")
    start_scheduler()
    
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AETHER Geospatial AI - Backend API",
    lifespan=lifespan
)

app.include_router(v1_router, prefix="/api/v1", tags=["Geospatial Analysis"])

@app.get("/")
def health_check():
    return {"status": "online", "system": "AETHER CORE", "environment": settings.ENVIRONMENT}