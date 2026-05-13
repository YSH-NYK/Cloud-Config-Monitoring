"""Snapshot management service for storing and retrieving configuration snapshots."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging


class SnapshotManager:
    """Manages configuration snapshots with timestamped storage."""
    
    def __init__(
        self,
        snapshots_dir: str = "snapshots",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize snapshot manager.
        
        Args:
            snapshots_dir: Base directory for storing snapshots
            logger: Logger instance
        """
        self.snapshots_dir = snapshots_dir
        self.logger = logger or logging.getLogger(__name__)
        # Removed directory creation - using database-only storage
    
    def save_snapshot(
        self,
        service_type: str,
        data: List[Dict[str, Any]],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Save a configuration snapshot.
        
        Args:
            service_type: Type of service (cos, iam, vpc, vsi, security)
            data: Configuration data to save
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            Path to saved snapshot file
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Format timestamp for filename (ISO 8601 compatible)
        timestamp_str = timestamp.strftime('%Y-%m-%dT%H-%M-%S')
        
        # Create snapshot filename
        filename = f"{timestamp_str}.json"
        service_dir = os.path.join(self.snapshots_dir, service_type)
        filepath = os.path.join(service_dir, filename)
        
        # Prepare snapshot with metadata
        snapshot = {
            "timestamp": timestamp.isoformat() + 'Z',
            "service_type": service_type,
            "resource_count": len(data),
            "resources": data
        }
        
        # Save snapshot
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        self.logger.info(
            f"Saved {service_type} snapshot with {len(data)} resources to {filepath}"
        )
        
        return filepath
    
    def get_latest_snapshot(
        self,
        service_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent snapshot for a service type.
        
        Args:
            service_type: Type of service
            
        Returns:
            Snapshot data or None if no snapshots exist
        """
        service_dir = os.path.join(self.snapshots_dir, service_type)
        
        if not os.path.exists(service_dir):
            self.logger.warning(f"No snapshot directory found for {service_type}")
            return None
        
        # Get all snapshot files
        snapshot_files = sorted(
            [f for f in os.listdir(service_dir) if f.endswith('.json')],
            reverse=True
        )
        
        if not snapshot_files:
            self.logger.debug(f"No snapshots found for {service_type}")
            return None
        
        # Load the latest snapshot
        latest_file = os.path.join(service_dir, snapshot_files[0])
        with open(latest_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        self.logger.debug(f"Loaded latest {service_type} snapshot from {latest_file}")
        return snapshot
    
    def get_previous_snapshot(
        self,
        service_type: str,
        before_timestamp: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the snapshot before a given timestamp.
        
        Args:
            service_type: Type of service
            before_timestamp: Get snapshot before this time (defaults to now)
            
        Returns:
            Snapshot data or None if no previous snapshot exists
        """
        service_dir = os.path.join(self.snapshots_dir, service_type)
        
        if not os.path.exists(service_dir):
            return None
        
        # Get all snapshot files
        snapshot_files = sorted(
            [f for f in os.listdir(service_dir) if f.endswith('.json')],
            reverse=True
        )
        
        if len(snapshot_files) < 2:
            self.logger.debug(f"Not enough snapshots for comparison in {service_type}")
            return None
        
        # If before_timestamp is provided, find the snapshot before it
        if before_timestamp:
            timestamp_str = before_timestamp.strftime('%Y-%m-%dT%H-%M-%S')
            for snapshot_file in snapshot_files:
                if snapshot_file.replace('.json', '') < timestamp_str:
                    filepath = os.path.join(service_dir, snapshot_file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
            return None
        
        # Otherwise, return the second most recent snapshot
        previous_file = os.path.join(service_dir, snapshot_files[1])
        with open(previous_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        self.logger.debug(f"Loaded previous {service_type} snapshot from {previous_file}")
        return snapshot
    
    def list_snapshots(
        self,
        service_type: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all snapshots for a service type.
        
        Args:
            service_type: Type of service
            limit: Optional limit on number of snapshots to return
            
        Returns:
            List of snapshot metadata
        """
        service_dir = os.path.join(self.snapshots_dir, service_type)
        
        if not os.path.exists(service_dir):
            return []
        
        snapshot_files = sorted(
            [f for f in os.listdir(service_dir) if f.endswith('.json')],
            reverse=True
        )
        
        if limit:
            snapshot_files = snapshot_files[:limit]
        
        snapshots = []
        for snapshot_file in snapshot_files:
            filepath = os.path.join(service_dir, snapshot_file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    snapshot = json.load(f)
                    snapshots.append({
                        'filename': snapshot_file,
                        'filepath': filepath,
                        'timestamp': snapshot.get('timestamp'),
                        'resource_count': snapshot.get('resource_count', 0)
                    })
            except Exception as e:
                self.logger.error(f"Error reading snapshot {filepath}: {str(e)}")
        
        return snapshots
    
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
        service_dir = os.path.join(self.snapshots_dir, service_type)
        
        if not os.path.exists(service_dir):
            return 0
        
        snapshot_files = sorted(
            [f for f in os.listdir(service_dir) if f.endswith('.json')],
            reverse=True
        )
        
        if len(snapshot_files) <= keep_count:
            return 0
        
        # Delete old snapshots
        deleted_count = 0
        for snapshot_file in snapshot_files[keep_count:]:
            filepath = os.path.join(service_dir, snapshot_file)
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                self.logger.error(f"Error deleting snapshot {filepath}: {str(e)}")
        
        self.logger.info(
            f"Cleaned up {deleted_count} old {service_type} snapshots, "
            f"keeping {keep_count} most recent"
        )
        
        return deleted_count


