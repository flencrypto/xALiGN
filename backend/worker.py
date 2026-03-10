"""Standalone background worker entry-point.

Runs the APScheduler intelligence-collection jobs independently of the API
server so the workload can be scaled (and deployed) separately in Kubernetes.

Usage::

    python -m backend.worker
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("align.worker")


async def _main() -> None:
    from backend.services.scheduler import scheduler, setup_scheduler

    # setup_scheduler registers all jobs AND starts the scheduler internally.
    # Passing None for the app argument is safe; the app ref is reserved for
    # future lifespan hooks and is not used by the scheduler itself.
    setup_scheduler(None)  # type: ignore[arg-type]

    logger.info("Worker scheduler started – waiting for jobs…")
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
        logger.info("Worker scheduler stopped.")


if __name__ == "__main__":
    asyncio.run(_main())
