"""Background scheduler for Intelligence Collection Layer (BATCH 1).

Uses APScheduler's AsyncIOScheduler to run all five collectors on a cron
schedule.  The scheduler is wired into FastAPI's lifespan context via
``setup_scheduler(app)``.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("align.scheduler")

scheduler = AsyncIOScheduler()


def setup_scheduler(app) -> None:  # noqa: ARG001  (app reserved for future use)
    """Register all intelligence collection jobs and start the scheduler."""
    from backend.database import SessionLocal
    from backend.services.infra_monitor import run_infra_monitor
    from backend.services.job_signal_detector import run_job_signal_detector
    from backend.services.news_aggregator import run_news_aggregator
    from backend.services.planning_scraper import run_planning_scraper
    from backend.services.press_release_harvester import run_press_release_harvester

    async def _run(fn):
        """Create a short-lived DB session, invoke *fn*, then close it."""
        db = SessionLocal()
        try:
            count = await fn(db)
            logger.info("%s collected %d records", fn.__name__, count)
        except Exception as exc:
            logger.error("%s failed: %s", fn.__name__, exc)
        finally:
            db.close()

    # Import asyncio here to avoid circular issues at module load time
    import asyncio

    def _make_job(fn):
        """Return a plain callable that schedules the coroutine on the running loop."""

        def _job():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_run(fn))
            except RuntimeError:
                # No running loop – fall back to get_event_loop (test / edge-case scenarios)
                loop = asyncio.get_event_loop()
                loop.create_task(_run(fn))
            except Exception as exc:
                logger.error("Scheduler could not dispatch %s: %s", fn.__name__, exc)

        return _job

    scheduler.add_job(
        _make_job(run_news_aggregator),
        CronTrigger(hour="*/6"),
        id="news_aggregator",
        replace_existing=True,
    )
    scheduler.add_job(
        _make_job(run_planning_scraper),
        CronTrigger(hour="8"),
        id="planning_scraper",
        replace_existing=True,
    )
    scheduler.add_job(
        _make_job(run_press_release_harvester),
        CronTrigger(hour="*/4"),
        id="press_release_harvester",
        replace_existing=True,
    )
    scheduler.add_job(
        _make_job(run_job_signal_detector),
        CronTrigger(hour="6"),
        id="job_signal_detector",
        replace_existing=True,
    )
    scheduler.add_job(
        _make_job(run_infra_monitor),
        CronTrigger(hour="*/6"),
        id="infra_monitor",
        replace_existing=True,
    )

    # Daily briefing ingestion (runs at 07:30 UTC)
    from backend.services.briefing_ingestion import run_daily_briefing_ingestion

    def _briefing_job():
        """Run the daily briefing ingestion task."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        
        loop.create_task(run_daily_briefing_ingestion())

    scheduler.add_job(
        _briefing_job,
        CronTrigger(hour="7", minute="30"),
        id="daily_briefing_ingestion",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Intelligence collection scheduler started with 6 jobs (including daily briefing).")
