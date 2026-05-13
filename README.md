A comprehensive Python-based system for monitoring IBM Cloud infrastructure configurations and detecting configuration drift over time.

## Features

### Core Capabilities
- **Multi-Service Collection**: Collects configurations from COS, IAM, VPC, VSI, and Security services
- **Scheduled Monitoring**: Continuous monitoring with configurable collection intervals
- **Drift Detection**: Automatic detection of infrastructure configuration changes
- **Snapshot Management**: Timestamped storage of configuration snapshots
- **Drift Reporting**: Detailed reports of detected changes
- **Database Persistence**: Optional PostgreSQL storage for snapshots and drift history
- **Modular Architecture**: Extensible design for future enhancements

### Drift Detection
The system detects three types of changes:
- **Added Resources**: New resources that didn't exist in previous snapshot
- **Removed Resources**: Resources that existed before but are now gone
- **Modified Resources**: Resources with configuration changes

## Architecture

```
project/
├── collectors/          # Service-specific collectors
│   ├── cos_collector.py
│   ├── iam_collector.py
│   ├── vpc_collector.py
│   ├── vsi_collector.py
│   └── security_collector.py
├── services/           # Core services
│   ├── ibm_cloud_client.py      # IBM Cloud API client
│   ├── snapshot_manager.py      # Snapshot storage/retrieval
│   ├── drift_detector.py        # Drift detection engine
│   ├── scheduler_service.py     # Job scheduling
│   └── database_service.py      # Optional DB persistence
├── config/             # Configuration management
├── utils/              # Utility functions
├── snapshots/          # Configuration snapshots
│   ├── cos/
│   ├── iam/
│   ├── vpc/
│   ├── vsi/
│   └── security/
├── drift_reports/      # Drift detection reports
├── logs/               # Application logs
└── main.py            # Main application entry point
```

## Installation

### Prerequisites
- Python 3.8 or higher
- IBM Cloud account with API key
- (Optional) PostgreSQL database for persistence

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

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your IBM Cloud credentials
```

## Configuration

### Required Environment Variables

```bash
# IBM Cloud Credentials
IBM_CLOUD_API_KEY=your_api_key_here
IBM_CLOUD_ACCOUNT_ID=your_account_id_here
IBM_CLOUD_REGION=us-south

# Cloud Object Storage (if using COS)
IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
IBM_COS_API_KEY=your_cos_api_key_here
IBM_COS_INSTANCE_CRN=your_cos_instance_crn_here
```

### Optional Configuration

```bash
# Monitoring Mode
ENABLE_MONITORING=false  # Set to true for continuous monitoring

# Collection Intervals (minutes)
COS_COLLECTION_INTERVAL=5
IAM_COLLECTION_INTERVAL=15
VPC_COLLECTION_INTERVAL=10
VSI_COLLECTION_INTERVAL=10
SECURITY_COLLECTION_INTERVAL=10

# Snapshot Management
SNAPSHOTS_DIR=snapshots
DRIFT_REPORTS_DIR=drift_reports
SNAPSHOT_RETENTION_COUNT=10

# Database (Optional)
ENABLE_DATABASE=false
DATABASE_URL=postgresql://user:pass@localhost:5432/ibm_cloud_monitor
```

## Usage

### Continuous Monitoring Mode (Default)

Start the monitoring service:

```bash
python main.py
```

The monitoring service will:
1. Run continuously as a background service
2. Collect configurations at scheduled intervals
3. Automatically detect drift after each collection
4. Generate drift reports for changes
5. Clean up old snapshots based on retention policy

To stop monitoring, press `Ctrl+C`.

### One-Time Collection Mode

Run a single collection and drift detection:

```bash
python main.py --once
```

This will:
1. Collect current configurations from all services
2. Save snapshots with timestamps
3. Compare with previous snapshots (if available)
4. Generate drift reports for any detected changes
5. Exit after completion

## Output Structure

### Snapshots

Snapshots are stored in timestamped JSON files:

```
snapshots/
├── cos/
│   ├── 2026-05-13T14-00-00.json
│   └── 2026-05-13T14-05-00.json
├── iam/
│   ├── 2026-05-13T14-00-00.json
│   └── 2026-05-13T14-15-00.json
└── vpc/
    ├── 2026-05-13T14-00-00.json
    └── 2026-05-13T14-10-00.json
```

Each snapshot contains:
```json
{
  "timestamp": "2026-05-13T14:00:00Z",
  "service_type": "cos",
  "resource_count": 5,
  "resources": [...]
}
```

### Drift Reports

Drift reports are generated when changes are detected:

```
drift_reports/
├── cos_drift_2026-05-13T14-05-00.json
├── iam_drift_2026-05-13T14-15-00.json
└── drift_summary_20260513_140500.json
```

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
    "added": [...],
    "removed": [...],
    "modified": [
      {
        "resource_id": "bucket-123",
        "resource_type": "cos_bucket",
        "change_type": "modified",
        "changes": {
          "values_changed": {
            "configuration.public_access": {
              "old": false,
              "new": true
            }
          }
        }
      }
    ]
  }
}
```

## Database Persistence (Optional)

Enable PostgreSQL persistence for long-term storage:

1. **Setup PostgreSQL database**
```sql
CREATE DATABASE ibm_cloud_monitor;
```

2. **Configure environment**
```bash
ENABLE_DATABASE=true
DATABASE_URL=postgresql://username:password@localhost:5432/ibm_cloud_monitor
```

3. **Run the application**

The system will automatically:
- Create required tables
- Store snapshots in the database
- Store drift reports in the database
- Maintain both file-based and database storage

## Logging

Logs are written to:
- Console (stdout)
- Log file: `logs/ibm_cloud_collector.log`

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Configure via `LOG_LEVEL` environment variable.

## Drift Detection Details

The drift detector uses DeepDiff to compare snapshots and identifies:

### Added Resources
Resources present in current snapshot but not in previous snapshot.

### Removed Resources
Resources present in previous snapshot but not in current snapshot.

### Modified Resources
Resources present in both snapshots with configuration changes:
- **Value Changes**: Field values that changed
- **Type Changes**: Field types that changed
- **Items Added**: New fields added to configuration
- **Items Removed**: Fields removed from configuration
- **List Changes**: Items added/removed from lists

## Extensibility

The system is designed for future enhancements:

### Planned Features
- **Compliance Evaluation Layer**: Assess drift against compliance policies
- **AI-Powered Analysis**: Intelligent drift categorization and recommendations
- **Automated Remediation**: Automatic correction of unauthorized changes
- **Alert Integration**: Notifications via email, Slack, PagerDuty
- **Web Dashboard**: Real-time monitoring interface
- **Multi-Cloud Support**: Extend to AWS, Azure, GCP

### Adding New Collectors

1. Create a new collector in `collectors/`:
```python
from collectors.base_collector import BaseCollector

class NewServiceCollector(BaseCollector):
    def collect(self):
        # Implementation
        pass
```

2. Register in `main.py`
3. Add scheduling configuration