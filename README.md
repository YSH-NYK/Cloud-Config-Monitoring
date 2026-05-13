# IBM Cloud Configuration Monitor

A comprehensive Python-based system for monitoring IBM Cloud infrastructure configurations and detecting configuration drift over time.

## Features

### Core Capabilities
- **Multi-Service Collection**: Collects configurations from COS, IAM, VPC, VSI, and Security services
- **Scheduled Monitoring**: Continuous monitoring with configurable collection intervals
- **Drift Detection**: Automatic detection of infrastructure configuration changes using DeepDiff
- **PostgreSQL Storage**: Database-first architecture for snapshots and drift history
- **Snapshot Management**: Timestamped storage of configuration snapshots
- **Drift Reporting**: Detailed reports of detected changes
- **Modular Architecture**: Extensible design for future compliance evaluation and AI integration

### Drift Detection
The system detects three types of changes:
- **Added Resources**: New resources that didn't exist in previous snapshot
- **Removed Resources**: Resources that existed before but are now gone
- **Modified Resources**: Resources with configuration changes (values, types, fields, lists)

## Architecture

```
project/
├── collectors/          # Service-specific collectors
│   ├── base_collector.py
│   ├── cos_collector.py
│   ├── iam_collector.py
│   ├── vpc_collector.py
│   ├── vsi_collector.py
│   └── security_collector.py
├── services/           # Core services
│   ├── ibm_cloud_client.py      # IBM Cloud API client
│   ├── snapshot_manager.py      # Snapshot storage/retrieval
│   ├── drift_detector.py        # Drift detection engine
│   ├── scheduler_service.py     # APScheduler job scheduling
│   └── database_service.py      # PostgreSQL persistence
├── config/             # Configuration management
│   └── settings.py
├── utils/              # Utility functions
│   ├── json_handler.py
│   └── logger.py
├── logs/               # Application logs
├── docs/               # Documentation
└── main.py            # Main application entry point
```

## Installation

### Prerequisites
- Python 3.8 or higher
- IBM Cloud account with API key
- PostgreSQL database (recommended for production use)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd IBMCloud-Config-fetch
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup PostgreSQL database**
```sql
CREATE DATABASE ibm_config_monitor;
CREATE USER ibm_monitor WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ibm_config_monitor TO ibm_monitor;
```

5. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

### Required Environment Variables

```bash
# IBM Cloud Credentials
IBM_CLOUD_API_KEY=your_api_key_here
IBM_CLOUD_ACCOUNT_ID=your_account_id_here
IBM_CLOUD_REGION=us-south

# Cloud Object Storage (if using COS collector)
IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
IBM_COS_API_KEY=your_cos_api_key_here
IBM_COS_INSTANCE_CRN=your_cos_instance_crn_here

# Database Configuration
ENABLE_DATABASE=true
DATABASE_URL=postgresql://ibm_monitor:your_password@localhost:5432/ibm_config_monitor
```

### Optional Configuration

```bash
# Monitoring Mode (default: false for one-time collection)
ENABLE_MONITORING=true  # Set to true for continuous monitoring

# Collection Intervals (minutes)
COS_COLLECTION_INTERVAL=5
IAM_COLLECTION_INTERVAL=15
VPC_COLLECTION_INTERVAL=10
VSI_COLLECTION_INTERVAL=10
SECURITY_COLLECTION_INTERVAL=10

# Snapshot Retention
SNAPSHOT_RETENTION_COUNT=10  # Keep last N snapshots per service

# Logging
LOG_LEVEL=INFO
```

## Usage

### Continuous Monitoring Mode (Default)

Start the monitoring service:

```bash
python main.py
```

The monitoring service will:
1. Run continuously as a background service
2. Collect configurations at scheduled intervals:
   - COS: every 5 minutes
   - IAM: every 15 minutes
   - VPC/VSI/Security: every 10 minutes
3. Automatically detect drift after each collection
4. Store snapshots and drift reports in PostgreSQL
5. Clean up old snapshots based on retention policy

To stop monitoring, press `Ctrl+C`.

### One-Time Collection Mode

Run a single collection and drift detection:

```bash
python main.py --once
```

This will:
1. Collect current configurations from all services
2. Save snapshots to database
3. Compare with previous snapshots (if available)
4. Generate drift reports for any detected changes
5. Exit after completion

## Storage Architecture

### Database-First Design

When `ENABLE_DATABASE=true` (recommended):
- ✅ All snapshots stored in PostgreSQL `snapshots` table
- ✅ All drift reports stored in PostgreSQL `drift_reports` table
- ✅ No local JSON files created
- ✅ Efficient querying and retention management

### Database Schema

**Snapshots Table:**
```sql
- id (primary key)
- service_type (cos, iam, vpc, vsi, security)
- timestamp (ISO 8601 format)
- resource_count
- snapshot_data (JSONB)
- created_at
```

**Drift Reports Table:**
```sql
- id (primary key)
- service_type
- detection_timestamp
- has_drift (boolean)
- total_changes
- added_count
- removed_count
- modified_count
- drift_data (JSONB)
- created_at
```

### Snapshot Structure

Each snapshot contains:
```json
{
  "timestamp": "2026-05-13T14:00:00Z",
  "service_type": "cos",
  "resource_count": 5,
  "resources": [
    {
      "id": "bucket-123",
      "name": "my-bucket",
      "configuration": {...}
    }
  ]
}
```

### Drift Report Structure

Example drift report:
```json
{
  "service_type": "cos",
  "detection_timestamp": "2026-05-13T14:05:00Z",
  "has_drift": true,
  "summary": {
    "total_changes": 3,
    "added_count": 1,
    "removed_count": 0,
    "modified_count": 2
  },
  "changes": {
    "added": [
      {
        "resource_id": "bucket-456",
        "resource_type": "cos_bucket",
        "change_type": "added"
      }
    ],
    "removed": [],
    "modified": [
      {
        "resource_id": "bucket-123",
        "resource_type": "cos_bucket",
        "change_type": "modified",
        "changes": {
          "values_changed": {
            "root['configuration']['public_access']": {
              "old_value": false,
              "new_value": true
            }
          }
        }
      }
    ]
  }
}
```

## Querying Data

### Using psql

```bash
# Connect to database
psql -U ibm_monitor -d ibm_config_monitor

# View recent snapshots
SELECT service_type, timestamp, resource_count
FROM snapshots
ORDER BY timestamp DESC
LIMIT 10;

# View drift reports with changes
SELECT service_type, detection_timestamp, total_changes, has_drift
FROM drift_reports
WHERE has_drift = true
ORDER BY detection_timestamp DESC;

# Query specific service snapshots
SELECT * FROM snapshots
WHERE service_type = 'cos'
ORDER BY timestamp DESC
LIMIT 5;
```

### Using pgAdmin

1. Connect to `ibm_config_monitor` database
2. Browse tables: `snapshots`, `drift_reports`
3. Use Query Tool for custom queries
4. View JSONB data in formatted view

## Logging

Logs are written to:
- **Console**: Real-time output with color coding
- **Log file**: `logs/ibm_cloud_collector.log` (rotating, max 10MB)

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Configure via `LOG_LEVEL` environment variable.

## Drift Detection Details

The drift detector uses **DeepDiff** library to compare snapshots and identifies:

### Added Resources
Resources present in current snapshot but not in previous snapshot.

### Removed Resources
Resources present in previous snapshot but not in current snapshot.

### Modified Resources
Resources present in both snapshots with configuration changes:
- **Value Changes**: Field values that changed (e.g., `public_access: false → true`)
- **Type Changes**: Field types that changed (e.g., `string → integer`)
- **Items Added**: New fields added to configuration
- **Items Removed**: Fields removed from configuration
- **List Changes**: Items added/removed from arrays

### Change Detection Logic

```python
# Example: Detecting bucket configuration change
old_snapshot = {
  "bucket-123": {
    "name": "my-bucket",
    "public_access": false
  }
}

new_snapshot = {
  "bucket-123": {
    "name": "my-bucket",
    "public_access": true  # Changed!
  }
}

# Drift detector identifies:
# - Modified resource: bucket-123
# - Changed field: public_access (false → true)
```

## Extensibility

The system is designed for future enhancements:

### Planned Features
- **Compliance Evaluation Layer**: Assess drift against compliance policies (CIS, NIST, PCI-DSS)
- **AI-Powered Analysis**: Intelligent drift categorization and recommendations
- **Automated Remediation**: Automatic correction of unauthorized changes
- **Alert Integration**: Notifications via email, Slack, PagerDuty, webhooks
- **Web Dashboard**: Real-time monitoring interface with charts and graphs
- **Multi-Cloud Support**: Extend to AWS, Azure, GCP

### Adding New Collectors

To add support for a new IBM Cloud service:

1. **Create a new collector class** in `collectors/`:

```python
# collectors/new_service_collector.py
from typing import List, Dict, Any
from collectors.base_collector import BaseCollector

class NewServiceCollector(BaseCollector):
    """Collector for New IBM Cloud Service"""
    
    def __init__(self, client):
        super().__init__(client, service_type="new_service")
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect configurations from the new service.
        
        Returns:
            List of normalized resource dictionaries
        """
        try:
            self.logger.info(f"Collecting {self.service_type} configurations...")
            
            # Use IBM Cloud SDK to fetch resources
            resources = self._fetch_resources()
            
            # Normalize the data
            normalized = self._normalize_resources(resources)
            
            self.logger.info(f"Collected {len(normalized)} {self.service_type} resources")
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error collecting {self.service_type}: {e}")
            return []
    
    def _fetch_resources(self) -> List[Any]:
        """Fetch resources using IBM Cloud SDK"""
        # Implement SDK calls here
        pass
    
    def _normalize_resources(self, resources: List[Any]) -> List[Dict[str, Any]]:
        """Normalize resources to standard format"""
        normalized = []
        for resource in resources:
            normalized.append({
                "id": resource.id,
                "name": resource.name,
                "type": "new_service_resource",
                "configuration": {
                    # Extract relevant configuration
                }
            })
        return normalized
```

2. **Register the collector** in `main.py`:

```python
from collectors.new_service_collector import NewServiceCollector

# In IBMCloudCollector.__init__()
self.collectors = {
    "cos": COSCollector(self.client),
    "iam": IAMCollector(self.client),
    "vpc": VPCCollector(self.client),
    "vsi": VSICollector(self.client),
    "security": SecurityCollector(self.client),
    "new_service": NewServiceCollector(self.client),  # Add here
}
```

3. **Add scheduling configuration** in `config/settings.py`:

```python
self.new_service_collection_interval: int = int(
    os.getenv("NEW_SERVICE_COLLECTION_INTERVAL", "10")
)
```

4. **Update `.env.example`**:

```bash
# New Service Collection Interval (minutes)
NEW_SERVICE_COLLECTION_INTERVAL=10
```

5. **Add scheduler job** in `main.py`:

```python
if self.settings.enable_monitoring:
    # Existing jobs...
    
    # Add new service job
    self.scheduler.add_job(
        service_type="new_service",
        interval_minutes=self.settings.new_service_collection_interval
    )
```

That's it! The new collector will automatically:
- Be scheduled for periodic collection
- Have snapshots stored in the database
- Participate in drift detection
- Generate drift reports when changes occur