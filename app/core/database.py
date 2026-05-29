from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
from app.core.config import settings

# Use aiosqlite driver for async SQLite
# Convert sqlite:///... to sqlite+aiosqlite:///...
DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class RiskAnalysis(Base):
    __tablename__ = "risk_analyses"

    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String, default="")
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    risk_type = Column(String)  # 'flood', 'drought', 'heatwave', 'storm', 'landslide', 'wildfire', 'multi'
    probability_score = Column(Float)
    severity = Column(String)  # 'LOW', 'MOD', 'HIGH', 'CRIT'
    geom_wkt = Column(String)
    # Extended climate snapshot
    temperature_c = Column(Float, default=0.0)
    apparent_temperature_c = Column(Float, default=0.0)
    precipitation_mm = Column(Float, default=0.0)
    daily_precipitation_mm = Column(Float, default=0.0)
    soil_moisture = Column(Float, default=0.0)
    humidity_percent = Column(Float, default=0.0)
    wind_speed_kmh = Column(Float, default=0.0)
    wind_gusts_kmh = Column(Float, default=0.0)
    surface_pressure_hpa = Column(Float, default=0.0)
    elevation_meters = Column(Float, default=0.0)
    # Multi-risk JSON summary (stored as text for SQLite compatibility)
    risks_json = Column(Text, default="")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RegionSubscription(Base):
    __tablename__ = "region_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String, unique=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_analyzed_at = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer)
    region_name = Column(String, default="")
    risk_type = Column(String, default="")
    message = Column(String)
    severity = Column(String, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)