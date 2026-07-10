"""
Background scheduler for automatic knowledge acquisition.

Runs a scraping pass over all enabled sources every SCRAPER_INTERVAL_HOURS hours.
Can also be triggered on-demand via trigger_now() from the sources API.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from utils.logger import get_logger
import config

logger = get_logger()
_scheduler: BackgroundScheduler | None = None

# These are set at startup by main.py
_db = None
_scraper_module = None


def _run_learning():
    if _db is None or _scraper_module is None:
        return
    sources = [s for s in _db.list_sources() if s["enabled"]]
    logger.info("Scheduled learning started — %d sources", len(sources))
    for source in sources:
        try:
            count = _scraper_module.learn_from_source(source)
            _db.update_source_fetch(source["id"], count)
            _db.log_learning(source["name"], count)
        except Exception as e:
            logger.error("Learning error for %s: %s", source["name"], e)
    logger.info("Scheduled learning complete.")


def start(db, scraper_module):
    global _scheduler, _db, _scraper_module
    _db = db
    _scraper_module = scraper_module

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _run_learning,
        trigger="interval",
        hours=config.SCRAPER_INTERVAL_HOURS,
        id="auto_learn",
    )
    _scheduler.start()
    logger.info("Scheduler started — learning every %dh", config.SCRAPER_INTERVAL_HOURS)


def stop():
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


def trigger_now():
    """Manually trigger a learning run (called from the API)."""
    import threading
    t = threading.Thread(target=_run_learning, daemon=True)
    t.start()
