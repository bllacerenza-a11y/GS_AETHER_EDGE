import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal, RegionSubscription
from app.api.v1_router import _run_full_analysis

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scan_monitored_regions():
    """Background job that scans all subscribed regions for risks."""
    logger.info("Starting background scan for monitored regions...")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RegionSubscription).filter(RegionSubscription.is_active == True))
        subscriptions = result.scalars().all()
        
        if not subscriptions:
            logger.info("No active subscriptions found. Skipping scan.")
            return

        for sub in subscriptions:
            logger.info(f"Scanning region: {sub.region_name}")
            try:
                # Run the full analysis. If high risks are found, it automatically generates alerts inside the db
                await _run_full_analysis(sub.latitude, sub.longitude, sub.region_name, db)
                
                # Update last analyzed timestamp
                sub.last_analyzed_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to scan region {sub.region_name}: {e}")
                await db.rollback()
                
    logger.info("Background scan completed.")

def start_scheduler():
    """Initializes and starts the background worker."""
    # Run every 2 hours in production, but we'll set it to run every 5 minutes for demonstration
    scheduler.add_job(scan_monitored_regions, 'interval', minutes=5, id='climate_scan_job', replace_existing=True)
    scheduler.start()
    logger.info("APScheduler started successfully. Autonomous monitoring active.")
