"""
APScheduler background task: polls NASA NeoWs every N minutes,
ingests new data, and fires WebSocket alerts for threshold breaches.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import get_settings
from backend.database import AsyncSessionLocal
from backend.services import neo_service

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler: AsyncIOScheduler | None = None


async def _poll_job():
    logger.info("Polling NASA NeoWs feed...")
    async with AsyncSessionLocal() as db:
        try:
            alert_ids = await neo_service.ingest_neows(db)
            await db.commit()
            if alert_ids:
                logger.warning(f"Alert threshold crossed for NEO ids: {alert_ids}")
                # Fire WebSocket alerts for each breaching NEO
                from backend.routers.alerts import fire_alert
                for neo_id in alert_ids:
                    neo = await neo_service.get_neo(db, neo_id)
                    if neo:
                        # Find latest approach
                        history = await neo_service.get_neo_history(db, neo_id, limit=1)
                        if history:
                            await fire_alert(
                                db=db,
                                neo_id=neo_id,
                                neo_name=neo.name,
                                miss_ld=history[0]["miss_distance_ld"],
                                approach_date=history[0]["approach_date"],
                            )
                await db.commit()
        except Exception as exc:
            logger.error(f"NeoWs poll failed: {exc}", exc_info=True)
            await db.rollback()


def start_scheduler():
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _poll_job,
        trigger=IntervalTrigger(minutes=settings.poll_interval_minutes),
        id="neows_poll",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        f"Scheduler started — polling every {settings.poll_interval_minutes} min"
    )


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
