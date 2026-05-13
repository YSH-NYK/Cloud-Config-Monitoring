"""Database service for optional PostgreSQL persistence of snapshots and drift history."""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()


class Snapshot(Base):
    """Snapshot model for database storage."""
    
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    resource_count = Column(Integer, nullable=False)
    resources = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DriftReport(Base):
    """Drift report model for database storage."""
    
    __tablename__ = 'drift_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_type = Column(String(50), nullable=False, index=True)
    detection_timestamp = Column(DateTime, nullable=False, index=True)
    has_drift = Column(Boolean, nullable=False, index=True)
    total_changes = Column(Integer, nullable=False)
    added_count = Column(Integer, nullable=False)
    removed_count = Column(Integer, nullable=False)
    modified_count = Column(Integer, nullable=False)
    report_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseService:
    """Service for managing database operations."""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize database service.
        
        Args:
            database_url: PostgreSQL connection URL (e.g., postgresql://user:pass@localhost/dbname)
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self.enabled = False
        
        if database_url:
            try:
                self._initialize_database()
                self.enabled = True
                self.logger.info("Database service initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize database: {str(e)}")
                self.enabled = False
        else:
            self.logger.info("Database service disabled (no connection URL provided)")
    
    def _initialize_database(self) -> None:
        """Initialize database connection and create tables."""
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self.logger.debug("Database tables created/verified")
    
    def get_session(self) -> Optional[Session]:
        """
        Get a database session.
        
        Returns:
            Database session or None if database is disabled
        """
        if not self.enabled or not self.SessionLocal:
            return None
        return self.SessionLocal()
    
    def save_snapshot(
        self,
        service_type: str,
        timestamp: datetime,
        resources: List[Dict[str, Any]]
    ) -> bool:
        """
        Save a snapshot to the database.
        
        Args:
            service_type: Type of service
            timestamp: Snapshot timestamp
            resources: List of resources
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            snapshot = Snapshot(
                service_type=service_type,
                timestamp=timestamp,
                resource_count=len(resources),
                resources=resources
            )
            session.add(snapshot)
            session.commit()
            
            self.logger.debug(
                f"Saved {service_type} snapshot to database "
                f"({len(resources)} resources)"
            )
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error saving snapshot to database: {str(e)}")
            return False
        finally:
            session.close()
    
    def get_latest_snapshot(
        self,
        service_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest snapshot for a service type.
        
        Args:
            service_type: Type of service
            
        Returns:
            Snapshot data or None
        """
        if not self.enabled:
            return None
        
        session = self.get_session()
        if not session:
            return None
        
        try:
            snapshot = session.query(Snapshot)\
                .filter(Snapshot.service_type == service_type)\
                .order_by(Snapshot.timestamp.desc())\
                .first()
            
            if snapshot:
                return {
                    'timestamp': snapshot.timestamp.isoformat() + 'Z',
                    'service_type': snapshot.service_type,
                    'resource_count': snapshot.resource_count,
                    'resources': snapshot.resources
                }
            return None
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving snapshot from database: {str(e)}")
            return None
        finally:
            session.close()
    
    def save_drift_report(
        self,
        drift_report: Dict[str, Any]
    ) -> bool:
        """
        Save a drift report to the database.
        
        Args:
            drift_report: Drift detection report
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            summary = drift_report.get('summary', {})
            
            report = DriftReport(
                service_type=drift_report.get('service_type'),
                detection_timestamp=datetime.fromisoformat(
                    drift_report.get('detection_timestamp').replace('Z', '+00:00')
                ),
                has_drift=drift_report.get('has_drift', False),
                total_changes=summary.get('total_changes', 0),
                added_count=summary.get('added_count', 0),
                removed_count=summary.get('removed_count', 0),
                modified_count=summary.get('modified_count', 0),
                report_data=drift_report
            )
            session.add(report)
            session.commit()
            
            self.logger.debug(
                f"Saved {drift_report.get('service_type')} drift report to database"
            )
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error saving drift report to database: {str(e)}")
            return False
        finally:
            session.close()
    
    def get_drift_history(
        self,
        service_type: Optional[str] = None,
        limit: int = 100,
        only_with_drift: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get drift report history.
        
        Args:
            service_type: Optional filter by service type
            limit: Maximum number of reports to return
            only_with_drift: Only return reports with detected drift
            
        Returns:
            List of drift reports
        """
        if not self.enabled:
            return []
        
        session = self.get_session()
        if not session:
            return []
        
        try:
            query = session.query(DriftReport)
            
            if service_type:
                query = query.filter(DriftReport.service_type == service_type)
            
            if only_with_drift:
                query = query.filter(DriftReport.has_drift == True)
            
            reports = query.order_by(DriftReport.detection_timestamp.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    'id': report.id,
                    'service_type': report.service_type,
                    'detection_timestamp': report.detection_timestamp.isoformat() + 'Z',
                    'has_drift': report.has_drift,
                    'total_changes': report.total_changes,
                    'summary': {
                        'added_count': report.added_count,
                        'removed_count': report.removed_count,
                        'modified_count': report.modified_count
                    }
                }
                for report in reports
            ]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving drift history from database: {str(e)}")
            return []
        finally:
            session.close()
    
    def cleanup_old_snapshots(
        self,
        service_type: str,
        keep_count: int = 10
    ) -> int:
        """
        Remove old snapshots, keeping only the most recent ones.
        
        Args:
            service_type: Type of service
            keep_count: Number of recent snapshots to keep
            
        Returns:
            Number of snapshots deleted
        """
        if not self.enabled:
            return 0
        
        session = self.get_session()
        if not session:
            return 0
        
        try:
            # Get IDs of snapshots to keep
            keep_ids = session.query(Snapshot.id)\
                .filter(Snapshot.service_type == service_type)\
                .order_by(Snapshot.timestamp.desc())\
                .limit(keep_count)\
                .all()
            
            keep_ids = [id[0] for id in keep_ids]
            
            # Delete old snapshots
            deleted = session.query(Snapshot)\
                .filter(Snapshot.service_type == service_type)\
                .filter(~Snapshot.id.in_(keep_ids))\
                .delete(synchronize_session=False)
            
            session.commit()
            
            self.logger.info(
                f"Cleaned up {deleted} old {service_type} snapshots from database"
            )
            return deleted
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error cleaning up snapshots from database: {str(e)}")
            return 0
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful
        """
        if not self.enabled:
            return False
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            # Simple query to test connection
            session.execute("SELECT 1")
            session.close()
            return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            return False


