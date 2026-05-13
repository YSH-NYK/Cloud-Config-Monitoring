# Quick Start Guide

Get started with IBM Cloud Infrastructure Monitoring in 5 minutes!

## Prerequisites

- IBM Cloud account
- IBM Cloud API Key

# refer to IBM_CLOUD_CREDENTIALS_GUIDE to get these

## Installation

### 1. Clone and Setup

```bash

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
```

**Minimum required configuration:**
```bash
IBM_CLOUD_API_KEY=your_api_key_here
IBM_CLOUD_ACCOUNT_ID=your_account_id_here
IBM_CLOUD_REGION=us-south
```

### 3. Start Monitoring

```bash
python main.py
```

This will:
- ✅ Test connection to IBM Cloud
- ✅ Start continuous monitoring service
- ✅ Collect configurations at scheduled intervals
- ✅ Save snapshots to `snapshots/` directory
- ✅ Detect drift automatically
- ✅ Generate reports in `drift_reports/`

## Usage Examples

### Continuous Monitoring (Default)

```bash
# Start monitoring service (runs continuously)
python main.py
```

**Output:**
```
IBM Cloud Continuous Monitoring Started
Testing connection to IBM Cloud...
Connection test successful
Scheduled 5 jobs:
  - COS Collection (ID: cos_collection): Next run at 2026-05-13T14:05:00Z
  - IAM Collection (ID: iam_collection): Next run at 2026-05-13T14:15:00Z
  ...
Monitoring service is running. Press Ctrl+C to stop.
```

### One-Time Collection

```bash
# Run once and exit
python main.py --once
```

**Output:**
```
IBM Cloud One-Time Collection Started
Testing connection to IBM Cloud...
Connection test successful
Collecting cos configurations...
Collected 5 cos resources
Collecting iam configurations...
Collected 12 iam resources
...
Collection Complete!
Duration: 45.23 seconds
Total resources collected: 42
```

## Understanding the Output

### Snapshots

Located in `snapshots/` directory:

```
snapshots/
├── cos/
│   └── 2026-05-13T14-00-00.json    # COS snapshot at 2:00 PM
├── iam/
│   └── 2026-05-13T14-00-00.json    # IAM snapshot at 2:00 PM
└── vpc/
    └── 2026-05-13T14-00-00.json    # VPC snapshot at 2:00 PM
```

### Drift Reports

Located in `drift_reports/` directory:

```
drift_reports/
├── cos_drift_2026-05-13T14-05-00.json
└── drift_summary_20260513_140500.json
```

**Example drift report:**
```json
{
  "service_type": "cos",
  "has_drift": true,
  "summary": {
    "total_changes": 2,
    "added_count": 1,
    "removed_count": 0,
    "modified_count": 1
  }
}
```

## Configuration Options in .env

### Collection Intervals 

Customize how often each service is checked (in minutes):

```bash
COS_COLLECTION_INTERVAL=5      # Check COS every 5 minutes
IAM_COLLECTION_INTERVAL=15     # Check IAM every 15 minutes
VPC_COLLECTION_INTERVAL=10     # Check VPC every 10 minutes
VSI_COLLECTION_INTERVAL=10     # Check VSI every 10 minutes
SECURITY_COLLECTION_INTERVAL=10 # Check Security every 10 minutes
```

### Snapshot Retention

Control how many snapshots to keep:

```bash
SNAPSHOT_RETENTION_COUNT=10    # Keep last 10 snapshots per service
```

### Database Persistence (Optional)

Enable PostgreSQL for long-term storage:

```bash
ENABLE_DATABASE=true
DATABASE_URL=postgresql://user:pass@localhost:5432/ibm_config_monitor
```