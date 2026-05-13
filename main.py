#!/usr/bin/env python3
"""
IBM Cloud Infrastructure Monitoring and Configuration Drift Detection System

This application collects infrastructure configuration details from IBM Cloud,
stores snapshots, and detects configuration drift over time.

Supports two modes:
1. One-time collection mode (default)
2. Continuous monitoring mode (with --monitor flag)
"""

import sys
import signal
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import Settings
from services import (
    IBMCloudClient,
    SnapshotManager,
    DriftDetector,
    SchedulerService,
    DatabaseService
)
from collectors import (
    COSCollector,
    IAMCollector,
    VPCCollector,
    VSICollector,
    SecurityCollector
)
from utils import setup_logger, save_json


class IBMCloudMonitor:
    """Main orchestrator for IBM Cloud infrastructure monitoring and drift detection."""
    
    def __init__(self):
        """Initialize the monitor."""
        # Load settings
        self.settings = Settings()
        
        # Setup logger
        self.logger = setup_logger(
            log_level=self.settings.log_level,
            log_file=self.settings.log_file
        )
        
        # Validate settings
        if not self.settings.validate():
            self.logger.error("Invalid configuration. Please check your .env file.")
            sys.exit(1)
        
        # Initialize IBM Cloud client
        self.client = IBMCloudClient(
            api_key=self.settings.api_key,
            region=self.settings.region,
            cos_endpoint=self.settings.cos_endpoint,
            cos_api_key=self.settings.cos_api_key,
            cos_instance_crn=self.settings.cos_instance_crn,
            logger=self.logger
        )
        
        # Initialize snapshot manager
        self.snapshot_manager = SnapshotManager(
            snapshots_dir=self.settings.snapshots_dir,
            logger=self.logger
        )
        
        # Initialize drift detector
        self.drift_detector = DriftDetector(
            drift_reports_dir=self.settings.drift_reports_dir,
            logger=self.logger
        )
        
        # Initialize database service (optional)
        self.db_service = None
        if self.settings.enable_database and self.settings.database_url:
            self.db_service = DatabaseService(
                database_url=self.settings.database_url,
                logger=self.logger
            )
            if self.db_service.enabled:
                self.logger.info("Database persistence enabled")
        
        # Initialize scheduler (for monitoring mode)
        self.scheduler = None
        self.monitoring_active = False
        
        self.logger.info("IBM Cloud Monitor initialized")
    
    def test_connection(self) -> bool:
        """
        Test connection to IBM Cloud.
        
        Returns:
            bool: True if connection is successful
        """
        self.logger.info("Testing connection to IBM Cloud...")
        return self.client.test_connection()
    
    def collect_service(
        self,
        service_type: str,
        save_snapshot: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect configurations for a specific service type.
        
        Args:
            service_type: Type of service (cos, iam, vpc, vsi, security)
            save_snapshot: Whether to save snapshot
            
        Returns:
            List of collected resources
        """
        self.logger.info(f"Collecting {service_type} configurations...")
        
        try:
            # Select appropriate collector
            if service_type == 'cos':
                collector = COSCollector(
                    client=self.client,
                    region=self.settings.region,
                    logger=self.logger
                )
            elif service_type == 'iam':
                collector = IAMCollector(
                    client=self.client,
                    region=self.settings.region,
                    account_id=self.settings.account_id,
                    logger=self.logger
                )
            elif service_type == 'vpc':
                collector = VPCCollector(
                    client=self.client,
                    region=self.settings.region,
                    logger=self.logger
                )
            elif service_type == 'vsi':
                collector = VSICollector(
                    client=self.client,
                    region=self.settings.region,
                    logger=self.logger
                )
            elif service_type == 'security':
                collector = SecurityCollector(
                    client=self.client,
                    region=self.settings.region,
                    logger=self.logger
                )
            else:
                self.logger.error(f"Unknown service type: {service_type}")
                return []
            
            # Collect resources
            resources = collector.collect()
            
            # Save snapshot
            if save_snapshot and resources:
                snapshot_path = self.snapshot_manager.save_snapshot(
                    service_type=service_type,
                    data=resources
                )
                
                # Save to database if enabled
                if self.db_service and self.db_service.enabled:
                    self.db_service.save_snapshot(
                        service_type=service_type,
                        timestamp=datetime.utcnow(),
                        resources=resources
                    )
            
            self.logger.info(f"Collected {len(resources)} {service_type} resources")
            return resources
            
        except Exception as e:
            self.logger.error(f"Error collecting {service_type}: {str(e)}", exc_info=True)
            return []
    
    def detect_drift_for_service(self, service_type: str) -> Optional[Dict[str, Any]]:
        """
        Detect drift for a specific service type.
        
        Args:
            service_type: Type of service
            
        Returns:
            Drift report or None if no previous snapshot exists
        """
        self.logger.info(f"Detecting drift for {service_type}...")
        
        try:
            # Get current and previous snapshots
            current_snapshot = self.snapshot_manager.get_latest_snapshot(service_type)
            previous_snapshot = self.snapshot_manager.get_previous_snapshot(service_type)
            
            if not current_snapshot:
                self.logger.warning(f"No current snapshot found for {service_type}")
                return None
            
            if not previous_snapshot:
                self.logger.info(f"No previous snapshot found for {service_type} - skipping drift detection")
                return None
            
            # Detect drift
            drift_report = self.drift_detector.detect_drift(
                service_type=service_type,
                current_snapshot=current_snapshot,
                previous_snapshot=previous_snapshot
            )
            
            # Save drift report
            if drift_report.get('has_drift'):
                report_path = self.drift_detector.save_drift_report(drift_report)
                
                # Save to database if enabled
                if self.db_service and self.db_service.enabled:
                    self.db_service.save_drift_report(drift_report)
            
            return drift_report
            
        except Exception as e:
            self.logger.error(f"Error detecting drift for {service_type}: {str(e)}", exc_info=True)
            return None
    
    def collect_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect all configurations from IBM Cloud.
        
        Returns:
            Dictionary with collected resources by type
        """
        service_types = ['cos', 'iam', 'vpc', 'vsi', 'security']
        results = {}
        
        for service_type in service_types:
            self.logger.info("=" * 60)
            resources = self.collect_service(service_type, save_snapshot=True)
            results[service_type] = resources
        
        return results
    
    def detect_all_drift(self) -> List[Dict[str, Any]]:
        """
        Detect drift for all service types.
        
        Returns:
            List of drift reports
        """
        service_types = ['cos', 'iam', 'vpc', 'vsi', 'security']
        drift_reports = []
        
        for service_type in service_types:
            self.logger.info("=" * 60)
            drift_report = self.detect_drift_for_service(service_type)
            if drift_report:
                drift_reports.append(drift_report)
        
        return drift_reports
    
    def run_one_time_collection(self):
        """Run a one-time collection and drift detection."""
        self.logger.info("=" * 60)
        self.logger.info("IBM Cloud One-Time Collection Started")
        self.logger.info("=" * 60)
        
        start_time = datetime.utcnow()
        
        # Test connection
        if not self.test_connection():
            self.logger.error("Connection test failed. Exiting.")
            sys.exit(1)
        
        # Collect all configurations
        results = self.collect_all()
        
        # Detect drift
        self.logger.info("=" * 60)
        self.logger.info("Starting drift detection...")
        drift_reports = self.detect_all_drift()
        
        # Generate drift summary
        if drift_reports:
            drift_summary = self.drift_detector.generate_drift_summary(drift_reports)
            summary_path = save_json(
                data=drift_summary,
                filename="drift_summary",
                output_dir=self.settings.drift_reports_dir,
                use_timestamp=True
            )
            self.logger.info(f"Drift summary saved to {summary_path}")
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("Collection Complete!")
        self.logger.info("=" * 60)
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info(f"Total resources collected: {sum(len(r) for r in results.values())}")
        self.logger.info("Resource breakdown:")
        for service_type, resources in results.items():
            self.logger.info(f"  - {service_type}: {len(resources)}")
        
        if drift_reports:
            self.logger.info(f"\nDrift detected in {len([r for r in drift_reports if r.get('has_drift')])} services")
            for report in drift_reports:
                if report.get('has_drift'):
                    summary = report.get('summary', {})
                    self.logger.info(
                        f"  - {report.get('service_type')}: "
                        f"{summary.get('total_changes')} changes "
                        f"({summary.get('added_count')} added, "
                        f"{summary.get('removed_count')} removed, "
                        f"{summary.get('modified_count')} modified)"
                    )
        
        self.logger.info("=" * 60)
    
    def start_monitoring(self):
        """Start continuous monitoring mode with scheduled collections."""
        self.logger.info("=" * 60)
        self.logger.info("IBM Cloud Continuous Monitoring Started")
        self.logger.info("=" * 60)
        
        # Test connection
        if not self.test_connection():
            self.logger.error("Connection test failed. Exiting.")
            sys.exit(1)
        
        # Initialize scheduler
        self.scheduler = SchedulerService(logger=self.logger)
        
        # Schedule collection jobs
        self.scheduler.add_collection_job(
            job_id='cos_collection',
            collector_func=self._scheduled_collection,
            interval_minutes=self.settings.cos_collection_interval,
            service_type='cos'
        )
        
        self.scheduler.add_collection_job(
            job_id='iam_collection',
            collector_func=self._scheduled_collection,
            interval_minutes=self.settings.iam_collection_interval,
            service_type='iam'
        )
        
        self.scheduler.add_collection_job(
            job_id='vpc_collection',
            collector_func=self._scheduled_collection,
            interval_minutes=self.settings.vpc_collection_interval,
            service_type='vpc'
        )
        
        self.scheduler.add_collection_job(
            job_id='vsi_collection',
            collector_func=self._scheduled_collection,
            interval_minutes=self.settings.vsi_collection_interval,
            service_type='vsi'
        )
        
        self.scheduler.add_collection_job(
            job_id='security_collection',
            collector_func=self._scheduled_collection,
            interval_minutes=self.settings.security_collection_interval,
            service_type='security'
        )
        
        # Start scheduler
        self.scheduler.start()
        self.monitoring_active = True
        
        self.logger.info("Monitoring service is running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        try:
            while self.monitoring_active:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal...")
            self.stop_monitoring()
    
    def _scheduled_collection(self, service_type: str):
        """
        Scheduled collection job for a service type.
        
        Args:
            service_type: Type of service to collect
        """
        try:
            # Collect resources
            resources = self.collect_service(service_type, save_snapshot=True)
            
            # Detect drift
            drift_report = self.detect_drift_for_service(service_type)
            
            # Cleanup old snapshots
            self.snapshot_manager.cleanup_old_snapshots(
                service_type=service_type,
                keep_count=self.settings.snapshot_retention_count
            )
            
            if self.db_service and self.db_service.enabled:
                self.db_service.cleanup_old_snapshots(
                    service_type=service_type,
                    keep_count=self.settings.snapshot_retention_count
                )
            
        except Exception as e:
            self.logger.error(
                f"Error in scheduled collection for {service_type}: {str(e)}",
                exc_info=True
            )
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        if self.scheduler:
            self.logger.info("Stopping scheduler...")
            self.scheduler.stop(wait=True)
        self.monitoring_active = False
        self.logger.info("Monitoring service stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n\nReceived shutdown signal. Stopping monitoring...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        monitor = IBMCloudMonitor()
        
        # Check if one-time mode is requested
        if '--once' in sys.argv:
            monitor.run_one_time_collection()
        else:
            # Default to continuous monitoring
            monitor.start_monitoring()
            
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()


