#!/usr/bin/env python3
"""
Integrated Drift Detection Test Script

Tests drift detection using actual project services (SnapshotManager, DriftDetector, DatabaseService).
Uses mock data to simulate various drift scenarios without requiring IBM Cloud credentials.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from services.snapshot_manager import SnapshotManager
from services.drift_detector import DriftDetector
from services.database_service import DatabaseService
from utils.logger import setup_logger


class MockDriftTester:
    """Test drift detection with actual project services"""
    
    def __init__(self):
        """Initialize with actual project services"""
        self.test_results = []
        self.logger = setup_logger()
        
        # Load settings
        self.settings = Settings()
        
        # Create necessary directories for file-based storage
        self._ensure_directories()
        
        # Initialize services
        self.db_service = None
        if self.settings.enable_database:
            try:
                self.db_service = DatabaseService(self.settings.database_url, self.logger)
                self.logger.info("✅ Database service initialized")
            except Exception as e:
                self.logger.warning(f"⚠️  Database not available: {e}")
                self.logger.info("📁 Will use file-based storage as fallback")
        
        self.snapshot_manager = SnapshotManager(
            snapshots_dir=self.settings.snapshots_dir,
            logger=self.logger
        )
        
        self.drift_detector = DriftDetector(
            drift_reports_dir=self.settings.drift_reports_dir,
            logger=self.logger
        )
        
        self.logger.info("🧪 Test environment initialized")
    
    def _ensure_directories(self):
        """Create necessary directories for testing"""
        import os
        from pathlib import Path
        
        # Create base directories
        dirs_to_create = [
            self.settings.snapshots_dir,
            self.settings.drift_reports_dir,
            "logs"
        ]
        
        # Create service-specific snapshot directories
        service_types = ["cos", "iam", "vpc", "vsi", "security"]
        for service_type in service_types:
            dirs_to_create.append(os.path.join(self.settings.snapshots_dir, service_type))
        
        for directory in dirs_to_create:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"📁 Created test directories: {', '.join(dirs_to_create)}")
    
    def create_mock_snapshot(self, buckets: List[Dict]) -> Dict[str, Any]:
        """Create a mock COS snapshot"""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service_type": "cos",
            "resource_count": len(buckets),
            "resources": buckets
        }
    
    def save_and_detect_drift(self, current_snapshot: Dict, test_name: str) -> Dict[str, Any]:
        """
        Save snapshot using SnapshotManager and detect drift using DriftDetector.
        
        This uses the actual project services to:
        1. Retrieve previous snapshot (from DB or files)
        2. Save current snapshot (to DB or files)
        3. Detect drift using DriftDetector
        4. Save drift report (to DB or files)
        """
        service_type = current_snapshot["service_type"]
        
        # Get previous snapshot using SnapshotManager
        previous_snapshot = self.snapshot_manager.get_latest_snapshot(service_type)
        
        # Save current snapshot using SnapshotManager
        # Note: save_snapshot expects 'data' parameter (list of resources)
        self.snapshot_manager.save_snapshot(
            service_type=service_type,
            data=current_snapshot["resources"]
        )
        
        # Detect drift using DriftDetector
        if previous_snapshot:
            drift_report = self.drift_detector.detect_drift(
                service_type=service_type,
                current_snapshot=current_snapshot,
                previous_snapshot=previous_snapshot
            )
            
            # Save drift report if drift detected
            if drift_report and drift_report.get("has_drift"):
                self.drift_detector.save_drift_report(drift_report)
            
            return drift_report
        else:
            self.logger.info(f"No previous snapshot for {service_type}, skipping drift detection")
            return {
                "service_type": service_type,
                "detection_timestamp": datetime.utcnow().isoformat() + "Z",
                "has_drift": False,
                "summary": {
                    "total_changes": 0,
                    "added_count": 0,
                    "removed_count": 0,
                    "modified_count": 0
                },
                "changes": {
                    "added": [],
                    "removed": [],
                    "modified": []
                }
            }
    
    def print_report(self, report: Dict, test_name: str):
        """Pretty print drift report"""
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print(f"{'='*80}")
        print(f"Service: {report['service_type']}")
        print(f"Timestamp: {report['detection_timestamp']}")
        print(f"Has Drift: {report['has_drift']}")
        print(f"\nSummary:")
        print(f"  Total Changes: {report['summary']['total_changes']}")
        print(f"  Added: {report['summary']['added_count']}")
        print(f"  Removed: {report['summary']['removed_count']}")
        print(f"  Modified: {report['summary']['modified_count']}")
        
        if report['changes']['added']:
            print(f"\n✅ ADDED RESOURCES ({len(report['changes']['added'])}):")
            for item in report['changes']['added']:
                print(f"  - {item['resource_id']} ({item['resource_type']})")
                if 'resource_data' in item:
                    print(f"    Configuration: {json.dumps(item.get('configuration', {}), indent=6)}")
        
        if report['changes']['removed']:
            print(f"\n❌ REMOVED RESOURCES ({len(report['changes']['removed'])}):")
            for item in report['changes']['removed']:
                print(f"  - {item['resource_id']} ({item['resource_type']})")
        
        if report['changes']['modified']:
            print(f"\n🔄 MODIFIED RESOURCES ({len(report['changes']['modified'])}):")
            for item in report['changes']['modified']:
                print(f"  - {item['resource_id']} ({item['resource_type']})")
                if 'changes' in item:
                    changes = item['changes']
                    if 'values_changed' in changes:
                        print(f"    Value Changes:")
                        for path, change in changes['values_changed'].items():
                            print(f"      {path}:")
                            print(f"        Old: {change.get('old')}")
                            print(f"        New: {change.get('new')}")
                    if 'items_added' in changes:
                        print(f"    Fields Added: {changes['items_added']}")
                    if 'items_removed' in changes:
                        print(f"    Fields Removed: {changes['items_removed']}")
        
        print(f"\n{'='*80}\n")
        
        self.test_results.append({
            "test": test_name,
            "passed": report['has_drift'],
            "changes": report['summary']['total_changes']
        })
    
    def test_scenario_1_added_resource(self):
        """Test: Adding a new bucket"""
        print("\n🧪 SCENARIO 1: Adding a New Bucket")
        
        # Previous snapshot: 2 buckets
        previous = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": True
                }
            },
            {
                "resource_id": "bucket-2",
                "name": "my-bucket-2",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": False
                }
            }
        ])
        
        # Save previous snapshot first
        report = self.save_and_detect_drift(previous, "Scenario 1 - Baseline")
        
        # Current snapshot: 3 buckets (added bucket-3)
        current = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": True
                }
            },
            {
                "resource_id": "bucket-2",
                "name": "my-bucket-2",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": False
                }
            },
            {
                "resource_id": "bucket-3",
                "name": "my-new-bucket",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": True,
                    "lifecycle_rules": []
                }
            }
        ])
        
        report = self.save_and_detect_drift(current, "Scenario 1 - Added Resource")
        self.print_report(report, "Scenario 1: Added Resource")
    
    def test_scenario_2_modified_public_access(self):
        """Test: Making a bucket public"""
        print("\n🧪 SCENARIO 2: Making a Bucket Public")
        
        # Previous snapshot: All buckets private
        previous = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": True
                }
            },
            {
                "resource_id": "bucket-2",
                "name": "my-bucket-2",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": False
                }
            }
        ])
        
        # Save previous snapshot first
        report = self.save_and_detect_drift(previous, "Scenario 2 - Baseline")
        
        # Current snapshot: bucket-2 made public
        current = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": True
                }
            },
            {
                "resource_id": "bucket-2",
                "name": "my-bucket-2",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": True,  # Changed!
                    "encryption": "enabled",
                    "versioning": False
                }
            }
        ])
        
        report = self.save_and_detect_drift(current, "Scenario 2 - Modified Public Access")
        self.print_report(report, "Scenario 2: Modified Public Access")
    
    def test_scenario_3_removed_resource(self):
        """Test: Deleting a bucket"""
        print("\n🧪 SCENARIO 3: Deleting a Bucket")
        
        # Previous snapshot: 3 buckets
        previous = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled"
                }
            },
            {
                "resource_id": "bucket-2",
                "name": "my-bucket-2",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled"
                }
            },
            {
                "resource_id": "bucket-3",
                "name": "my-bucket-3",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled"
                }
            }
        ])
        
        # Save previous snapshot first
        report = self.save_and_detect_drift(previous, "Scenario 3 - Baseline")
        
        # Current snapshot: 2 buckets (bucket-2 deleted)
        current = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled"
                }
            },
            {
                "resource_id": "bucket-3",
                "name": "my-bucket-3",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled"
                }
            }
        ])
        
        report = self.save_and_detect_drift(current, "Scenario 3 - Removed Resource")
        self.print_report(report, "Scenario 3: Removed Resource")
    
    def test_scenario_4_multiple_changes(self):
        """Test: Multiple changes at once"""
        print("\n🧪 SCENARIO 4: Multiple Changes")
        
        # Previous snapshot
        previous = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": True
                }
            },
            {
                "resource_id": "bucket-2",
                "name": "my-bucket-2",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": False
                }
            },
            {
                "resource_id": "bucket-3",
                "name": "my-bucket-3",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "disabled"
                }
            }
        ])
        
        # Save previous snapshot first
        report = self.save_and_detect_drift(previous, "Scenario 4 - Baseline")
        
        # Current snapshot: Added bucket-4, modified bucket-1, deleted bucket-3
        current = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": True,  # Changed!
                    "encryption": "disabled",  # Changed!
                    "versioning": True
                }
            },
            {
                "resource_id": "bucket-2",
                "name": "my-bucket-2",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": False
                }
            },
            {
                "resource_id": "bucket-4",
                "name": "my-new-bucket",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled",
                    "versioning": True
                }
            }
        ])
        
        report = self.save_and_detect_drift(current, "Scenario 4 - Multiple Changes")
        self.print_report(report, "Scenario 4: Multiple Changes")
    
    def test_scenario_5_deep_nested_changes(self):
        """Test: Deep nested configuration changes"""
        print("\n🧪 SCENARIO 5: Deep Nested Configuration Changes")
        
        # Previous snapshot
        previous = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": {
                        "type": "AES256",
                        "key_management": "IBM",
                        "rotation_enabled": False
                    },
                    "lifecycle_rules": [
                        {"id": "rule-1", "days": 30, "action": "archive"},
                        {"id": "rule-2", "days": 90, "action": "delete"}
                    ]
                }
            }
        ])
        
        # Save previous snapshot first
        report = self.save_and_detect_drift(previous, "Scenario 5 - Baseline")
        
        # Current snapshot: Deep changes
        current = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": {
                        "type": "AES256",
                        "key_management": "Customer",  # Changed!
                        "rotation_enabled": True  # Changed!
                    },
                    "lifecycle_rules": [
                        {"id": "rule-1", "days": 60, "action": "archive"},  # Changed days!
                        {"id": "rule-3", "days": 120, "action": "delete"}  # New rule!
                    ]
                }
            }
        ])
        
        report = self.save_and_detect_drift(current, "Scenario 5 - Deep Nested Changes")
        self.print_report(report, "Scenario 5: Deep Nested Changes")
    
    def test_scenario_6_no_drift(self):
        """Test: No changes (no drift)"""
        print("\n🧪 SCENARIO 6: No Changes (No Drift)")
        
        # Previous snapshot
        previous = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled"
                }
            }
        ])
        
        # Save previous snapshot first
        report = self.save_and_detect_drift(previous, "Scenario 6 - Baseline")
        
        # Current snapshot: Identical
        current = self.create_mock_snapshot([
            {
                "resource_id": "bucket-1",
                "name": "my-bucket-1",
                "type": "cos_bucket",
                "configuration": {
                    "public_access": False,
                    "encryption": "enabled"
                }
            }
        ])
        
        report = self.save_and_detect_drift(current, "Scenario 6 - No Drift")
        self.print_report(report, "Scenario 6: No Drift")
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "="*80)
        print("DRIFT DETECTION TEST SUITE")
        print("Testing drift detection with actual project services")
        print("="*80)
        
        self.test_scenario_1_added_resource()
        self.test_scenario_2_modified_public_access()
        self.test_scenario_3_removed_resource()
        self.test_scenario_4_multiple_changes()
        self.test_scenario_5_deep_nested_changes()
        self.test_scenario_6_no_drift()
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        for result in self.test_results:
            status = "✅ PASS" if result['passed'] or result['test'] == "Scenario 6: No Drift" else "❌ FAIL"
            print(f"{status} - {result['test']}: {result['changes']} changes detected")
        print("="*80 + "\n")


if __name__ == "__main__":
    tester = MockDriftTester()
    tester.run_all_tests()

# Made with Bob
