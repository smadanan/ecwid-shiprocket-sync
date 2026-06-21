"""
Background Scheduler for Automatic Syncing
Runs sync jobs on a schedule using APScheduler
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

logger = logging.getLogger(__name__)


class SyncScheduler:
    """Background scheduler for order syncing"""
    
    def __init__(self, integrator):
        """Initialize scheduler"""
        self.integrator = integrator
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Shutdown scheduler on app exit
        atexit.register(lambda: self.scheduler.shutdown())
    
    def schedule_daily_sync(self, hour: int = 0, minute: int = 0):
        """
        Schedule sync to run daily at specific time
        
        Args:
            hour: Hour (0-23) in UTC
            minute: Minute (0-59)
        """
        logger.info(f"Scheduling daily sync at {hour:02d}:{minute:02d} UTC")
        
        self.scheduler.add_job(
            self._sync_job,
            CronTrigger(hour=hour, minute=minute),
            id='daily_sync',
            name='Daily Order Sync',
            replace_existing=True
        )
    
    def schedule_interval_sync(self, hours: int = 6):
        """
        Schedule sync to run every N hours
        
        Args:
            hours: Interval in hours
        """
        logger.info(f"Scheduling sync every {hours} hours")
        
        self.scheduler.add_job(
            self._sync_job,
            'interval',
            hours=hours,
            id='interval_sync',
            name=f'Sync Every {hours} Hours',
            replace_existing=True
        )
    
    def _sync_job(self):
        """Background job to sync orders"""
        try:
            logger.info("=" * 60)
            logger.info("AUTOMATIC SYNC STARTED")
            logger.info("=" * 60)
            
            result = self.integrator.sync_orders(hours=24)
            
            logger.info("=" * 60)
            logger.info(f"AUTOMATIC SYNC COMPLETED")
            logger.info(f"Fetched: {result['fetched']}")
            logger.info(f"Uploaded: {result['uploaded']}")
            logger.info(f"Failed: {result['failed']}")
            logger.info(f"Skipped: {result['skipped']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Automatic sync failed: {str(e)}")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def pause(self):
        """Pause the scheduler"""
        self.scheduler.pause()
        logger.info("Scheduler paused")
    
    def resume(self):
        """Resume the scheduler"""
        self.scheduler.resume()
        logger.info("Scheduler resumed")
