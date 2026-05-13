"""Scheduler service for continuous infrastructure monitoring."""

import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


class SchedulerService:
    """Manages scheduled collection and monitoring jobs."""
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize scheduler service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1  # Only one instance of each job at a time
            }
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
        
        self.logger.info("Scheduler service initialized")
    
    def add_collection_job(
        self,
        job_id: str,
        collector_func: Callable,
        interval_minutes: int,
        service_type: str,
        **kwargs
    ) -> None:
        """
        Add a scheduled collection job.
        
        Args:
            job_id: Unique identifier for the job
            collector_func: Function to execute for collection
            interval_minutes: Interval in minutes between executions
            service_type: Type of service being collected
            **kwargs: Additional arguments to pass to collector_func
        """
        # Merge service_type into kwargs
        job_kwargs = {'service_type': service_type}
        job_kwargs.update(kwargs)
        
        self.scheduler.add_job(
            func=collector_func,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name=f"{service_type} Collection",
            kwargs=job_kwargs,
            replace_existing=True
        )
        
        self.logger.info(
            f"Added collection job '{job_id}' for {service_type} "
            f"(interval: {interval_minutes} minutes)"
        )
    
    def add_drift_detection_job(
        self,
        job_id: str,
        detector_func: Callable,
        interval_minutes: int,
        service_type: str,
        **kwargs
    ) -> None:
        """
        Add a scheduled drift detection job.
        
        Args:
            job_id: Unique identifier for the job
            detector_func: Function to execute for drift detection
            interval_minutes: Interval in minutes between executions
            service_type: Type of service being monitored
            **kwargs: Additional arguments to pass to detector_func
        """
        self.scheduler.add_job(
            func=detector_func,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name=f"{service_type} Drift Detection",
            kwargs=kwargs,
            replace_existing=True
        )
        
        self.logger.info(
            f"Added drift detection job '{job_id}' for {service_type} "
            f"(interval: {interval_minutes} minutes)"
        )
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Scheduler started")
            self._log_scheduled_jobs()
        else:
            self.logger.warning("Scheduler is already running")
    
    def stop(self, wait: bool = True) -> None:
        """
        Stop the scheduler.
        
        Args:
            wait: Whether to wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            self.logger.info("Scheduler stopped")
        else:
            self.logger.warning("Scheduler is not running")
    
    def pause(self) -> None:
        """Pause all scheduled jobs."""
        self.scheduler.pause()
        self.logger.info("Scheduler paused")
    
    def resume(self) -> None:
        """Resume all scheduled jobs."""
        self.scheduler.resume()
        self.logger.info("Scheduler resumed")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        Get information about all scheduled jobs.
        
        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            job_id: ID of the job to remove
            
        Returns:
            True if job was removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed job '{job_id}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove job '{job_id}': {str(e)}")
            return False
    
    def _job_executed_listener(self, event) -> None:
        """
        Listener for successful job executions.
        
        Args:
            event: Job execution event
        """
        job = self.scheduler.get_job(event.job_id)
        if job:
            self.logger.info(
                f"Job '{job.name}' (ID: {event.job_id}) executed successfully"
            )
    
    def _job_error_listener(self, event) -> None:
        """
        Listener for job execution errors.
        
        Args:
            event: Job error event
        """
        job = self.scheduler.get_job(event.job_id)
        job_name = job.name if job else event.job_id
        
        self.logger.error(
            f"Job '{job_name}' (ID: {event.job_id}) failed with error: {event.exception}",
            exc_info=True
        )
    
    def _log_scheduled_jobs(self) -> None:
        """Log information about all scheduled jobs."""
        jobs = self.get_jobs()
        if jobs:
            self.logger.info(f"Scheduled {len(jobs)} jobs:")
            for job in jobs:
                self.logger.info(
                    f"  - {job['name']} (ID: {job['id']}): "
                    f"Next run at {job['next_run_time']}"
                )
        else:
            self.logger.warning("No jobs scheduled")
    
    def is_running(self) -> bool:
        """
        Check if scheduler is running.
        
        Returns:
            True if scheduler is running
        """
        return self.scheduler.running
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Job status dictionary or None if not found
        """
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'pending': job.pending
            }
        return None


