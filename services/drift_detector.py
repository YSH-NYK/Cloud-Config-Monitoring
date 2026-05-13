"""Drift detection service for identifying infrastructure configuration changes."""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from deepdiff import DeepDiff
from pathlib import Path
import json


class DriftDetector:
    """Detects configuration drift between snapshots."""
    
    def __init__(
        self,
        drift_reports_dir: str = "drift_reports",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize drift detector.
        
        Args:
            drift_reports_dir: Directory for storing drift reports
            logger: Logger instance
        """
        self.drift_reports_dir = drift_reports_dir
        self.logger = logger or logging.getLogger(__name__)
        # Removed directory creation - using database-only storage
    
    def detect_drift(
        self,
        service_type: str,
        current_snapshot: Dict[str, Any],
        previous_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect drift between two snapshots.
        
        Args:
            service_type: Type of service being compared
            current_snapshot: Current configuration snapshot
            previous_snapshot: Previous configuration snapshot
            
        Returns:
            Drift detection report
        """
        self.logger.info(f"Detecting drift for {service_type}")
        
        # Extract resources from snapshots
        current_resources = current_snapshot.get('resources', [])
        previous_resources = previous_snapshot.get('resources', [])
        
        # Create resource maps by resource_id for efficient comparison
        current_map = {r.get('resource_id'): r for r in current_resources}
        previous_map = {r.get('resource_id'): r for r in previous_resources}
        
        # Detect changes
        added_resources = self._detect_added_resources(current_map, previous_map)
        removed_resources = self._detect_removed_resources(current_map, previous_map)
        modified_resources = self._detect_modified_resources(current_map, previous_map)
        
        # Calculate drift summary
        has_drift = bool(added_resources or removed_resources or modified_resources)
        total_changes = len(added_resources) + len(removed_resources) + len(modified_resources)
        
        # Create drift report
        drift_report = {
            "service_type": service_type,
            "detection_timestamp": datetime.utcnow().isoformat() + 'Z',
            "current_snapshot_timestamp": current_snapshot.get('timestamp'),
            "previous_snapshot_timestamp": previous_snapshot.get('timestamp'),
            "has_drift": has_drift,
            "summary": {
                "total_changes": total_changes,
                "added_count": len(added_resources),
                "removed_count": len(removed_resources),
                "modified_count": len(modified_resources)
            },
            "changes": {
                "added": added_resources,
                "removed": removed_resources,
                "modified": modified_resources
            }
        }
        
        if has_drift:
            self.logger.warning(
                f"Drift detected in {service_type}: "
                f"{len(added_resources)} added, "
                f"{len(removed_resources)} removed, "
                f"{len(modified_resources)} modified"
            )
        else:
            self.logger.info(f"No drift detected in {service_type}")
        
        return drift_report
    
    def _detect_added_resources(
        self,
        current_map: Dict[str, Dict[str, Any]],
        previous_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect resources that were added.
        
        Args:
            current_map: Current resources mapped by resource_id
            previous_map: Previous resources mapped by resource_id
            
        Returns:
            List of added resources with metadata
        """
        added = []
        for resource_id, resource in current_map.items():
            if resource_id not in previous_map:
                added.append({
                    "resource_id": resource_id,
                    "resource_type": resource.get('resource_type'),
                    "change_type": "added",
                    "resource": resource
                })
        return added
    
    def _detect_removed_resources(
        self,
        current_map: Dict[str, Dict[str, Any]],
        previous_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect resources that were removed.
        
        Args:
            current_map: Current resources mapped by resource_id
            previous_map: Previous resources mapped by resource_id
            
        Returns:
            List of removed resources with metadata
        """
        removed = []
        for resource_id, resource in previous_map.items():
            if resource_id not in current_map:
                removed.append({
                    "resource_id": resource_id,
                    "resource_type": resource.get('resource_type'),
                    "change_type": "removed",
                    "resource": resource
                })
        return removed
    
    def _detect_modified_resources(
        self,
        current_map: Dict[str, Dict[str, Any]],
        previous_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect resources that were modified.
        
        Args:
            current_map: Current resources mapped by resource_id
            previous_map: Previous resources mapped by resource_id
            
        Returns:
            List of modified resources with detailed changes
        """
        modified = []
        
        # Check resources that exist in both snapshots
        common_ids = set(current_map.keys()) & set(previous_map.keys())
        
        for resource_id in common_ids:
            current_resource = current_map[resource_id]
            previous_resource = previous_map[resource_id]
            
            # Compare configurations using DeepDiff
            # Exclude timestamp field from comparison
            diff = DeepDiff(
                previous_resource,
                current_resource,
                exclude_paths=["root['timestamp']"],
                ignore_order=True,
                report_repetition=True
            )
            
            if diff:
                # Parse the diff to extract meaningful changes
                changes = self._parse_deepdiff(diff)
                
                modified.append({
                    "resource_id": resource_id,
                    "resource_type": current_resource.get('resource_type'),
                    "change_type": "modified",
                    "changes": changes,
                    "current_state": current_resource,
                    "previous_state": previous_resource
                })
        
        return modified
    
    def _parse_deepdiff(self, diff: DeepDiff) -> Dict[str, Any]:
        """
        Parse DeepDiff output into a structured format.
        
        Args:
            diff: DeepDiff object
            
        Returns:
            Structured changes dictionary
        """
        changes = {}
        
        # Values changed
        if 'values_changed' in diff:
            changes['values_changed'] = {}
            for path, change in diff['values_changed'].items():
                field_name = self._extract_field_name(path)
                changes['values_changed'][field_name] = {
                    'old': change.get('old_value'),
                    'new': change.get('new_value')
                }
        
        # Items added
        if 'dictionary_item_added' in diff:
            changes['items_added'] = [
                self._extract_field_name(path) 
                for path in diff['dictionary_item_added']
            ]
        
        # Items removed
        if 'dictionary_item_removed' in diff:
            changes['items_removed'] = [
                self._extract_field_name(path)
                for path in diff['dictionary_item_removed']
            ]
        
        # Type changes
        if 'type_changes' in diff:
            changes['type_changes'] = {}
            for path, change in diff['type_changes'].items():
                field_name = self._extract_field_name(path)
                changes['type_changes'][field_name] = {
                    'old_type': str(change.get('old_type')),
                    'new_type': str(change.get('new_type'))
                }
        
        # Iterable changes (lists, sets)
        if 'iterable_item_added' in diff:
            changes['list_items_added'] = list(diff['iterable_item_added'].keys())
        
        if 'iterable_item_removed' in diff:
            changes['list_items_removed'] = list(diff['iterable_item_removed'].keys())
        
        return changes
    
    def _extract_field_name(self, path: str) -> str:
        """
        Extract field name from DeepDiff path.
        
        Args:
            path: DeepDiff path string
            
        Returns:
            Cleaned field name
        """
        # Remove 'root' prefix and clean up the path
        path = path.replace("root", "").strip("[]'\"")
        return path
    
    def save_drift_report(
        self,
        drift_report: Dict[str, Any]
    ) -> str:
        """
        Save drift report to file.
        
        Args:
            drift_report: Drift detection report
            
        Returns:
            Path to saved report file
        """
        service_type = drift_report.get('service_type', 'unknown')
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
        
        filename = f"{service_type}_drift_{timestamp}.json"
        filepath = Path(self.drift_reports_dir) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(drift_report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved drift report to {filepath}")
        
        return str(filepath)
    
    def generate_drift_summary(
        self,
        all_drift_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a summary of all drift reports.
        
        Args:
            all_drift_reports: List of drift reports from all services
            
        Returns:
            Consolidated drift summary
        """
        total_changes = 0
        services_with_drift = []
        
        for report in all_drift_reports:
            if report.get('has_drift'):
                services_with_drift.append(report.get('service_type'))
                total_changes += report.get('summary', {}).get('total_changes', 0)
        
        summary = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "total_services_checked": len(all_drift_reports),
            "services_with_drift": len(services_with_drift),
            "services_affected": services_with_drift,
            "total_changes_detected": total_changes,
            "service_reports": all_drift_reports
        }
        
        return summary


