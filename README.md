# IBM Cloud Configuration Collector

A Python-based tool that connects to IBM Cloud and fetches infrastructure configuration details, storing the collected data as structured JSON files.

## Features

- **Comprehensive Data Collection**: Collects configurations from multiple IBM Cloud services:
  - Cloud Object Storage (COS) buckets and configurations
  - IAM users, service IDs, access groups, and policies
  - VPC and networking configurations (VPCs, subnets, gateways, floating IPs, load balancers)
  - Virtual Server Instances (VSI) with detailed configurations
  - Security groups and network ACLs with firewall rules

- **Normalized JSON Output**: All collected data is normalized into a consistent JSON schema
- **Timestamped Files**: Outputs are saved with timestamps for historical tracking
- **Production-Ready**: Includes proper error handling, logging, and modular architecture
- **Extensible**: Clean modular structure allows easy addition of new collectors

## Project Structure

```
config_fetch/
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py        # Environment variable handling
├── collectors/            # Resource collectors
│   ├── __init__.py
│   ├── base_collector.py  # Base collector class
│   ├── cos_collector.py   # Cloud Object Storage
│   ├── iam_collector.py   # IAM configurations
│   ├── vpc_collector.py   # VPC and networking
│   ├── vsi_collector.py   # Virtual Server Instances
│   └── security_collector.py  # Security groups & ACLs
├── services/              # IBM Cloud service clients
│   ├── __init__.py
│   └── ibm_cloud_client.py
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── logger.py          # Logging setup
│   └── json_handler.py    # JSON operations
├── output/                # Output directory (created automatically)
├── logs/                  # Log files (created automatically)
├── main.py               # Main application entry point
├── requirements.txt      # Python dependencies
├── .env.example         # Example environment variables
└── README.md            # This file
```

## Prerequisites

- Python 3.8 or higher
- IBM Cloud account with appropriate permissions
- IBM Cloud API key
- IBM Cloud Account ID

## Installation

1. **Clone or download this project**

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and fill in your IBM Cloud credentials:
   ```env
   IBM_CLOUD_API_KEY=your_api_key_here
   IBM_CLOUD_ACCOUNT_ID=your_account_id_here
   IBM_CLOUD_REGION=us-south
   
   # Optional: Cloud Object Storage (if collecting COS data)
   IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
   IBM_COS_API_KEY=your_cos_api_key_here
   IBM_COS_INSTANCE_CRN=your_cos_instance_crn_here
   ```

## Configuration

### Required Environment Variables

- `IBM_CLOUD_API_KEY`: Your IBM Cloud API key
- `IBM_CLOUD_ACCOUNT_ID`: Your IBM Cloud account ID
- `IBM_CLOUD_REGION`: IBM Cloud region (default: us-south)

### Optional Environment Variables

- `IBM_COS_ENDPOINT`: Cloud Object Storage endpoint URL
- `IBM_COS_API_KEY`: Cloud Object Storage API key
- `IBM_COS_INSTANCE_CRN`: Cloud Object Storage instance CRN
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FILE`: Path to log file (default: logs/ibm_cloud_collector.log)
- `OUTPUT_DIR`: Output directory for JSON files (default: output)

### Getting IBM Cloud Credentials

**📖 For detailed step-by-step instructions with screenshots, see [docs/IBM_CLOUD_CREDENTIALS_GUIDE.md](docs/IBM_CLOUD_CREDENTIALS_GUIDE.md)**

#### Quick Reference:

1. **API Key**:
   - Go to IBM Cloud Console → Manage → Access (IAM) → API keys
   - Create a new API key or use an existing one

2. **Account ID**:
   - Go to IBM Cloud Console → Manage → Account
   - Copy your Account ID from the account settings

3. **COS Credentials** (optional - only if collecting COS data):
   - Go to your COS instance → Service credentials
   - Create new credentials or use existing ones
   - Copy the API key and instance CRN
   - Determine your endpoint: `https://s3.{region}.cloud-object-storage.appdomain.cloud`
   
   **Common COS Endpoints**:
   - US South: `https://s3.us-south.cloud-object-storage.appdomain.cloud`
   - US East: `https://s3.us-east.cloud-object-storage.appdomain.cloud`
   - EU Germany: `https://s3.eu-de.cloud-object-storage.appdomain.cloud`
   - EU UK: `https://s3.eu-gb.cloud-object-storage.appdomain.cloud`

## Usage

### Basic Usage

Run the collector:
```bash
python main.py
```

Or make it executable:
```bash
chmod +x main.py
./main.py
```

### What Happens During Execution

1. **Connection Test**: Verifies connectivity to IBM Cloud
2. **Data Collection**: Collects configurations from all enabled services
3. **Data Normalization**: Converts all data to consistent JSON format
4. **File Output**: Saves timestamped JSON files to the output directory
5. **Summary Report**: Displays collection statistics and file locations

### Output Files

The tool generates the following files in the `output/` directory:

- `ibm_cloud_cos_YYYYMMDD_HHMMSS.json` - Cloud Object Storage configurations
- `ibm_cloud_iam_YYYYMMDD_HHMMSS.json` - IAM configurations
- `ibm_cloud_vpc_YYYYMMDD_HHMMSS.json` - VPC and networking configurations
- `ibm_cloud_vsi_YYYYMMDD_HHMMSS.json` - Virtual Server Instance configurations
- `ibm_cloud_security_YYYYMMDD_HHMMSS.json` - Security group and ACL configurations
- `ibm_cloud_all_resources_YYYYMMDD_HHMMSS.json` - Combined file with all resources
- `collection_summary_YYYYMMDD_HHMMSS.json` - Collection summary and statistics

## JSON Output Format

All resources follow this normalized schema:

```json
{
  "resource_id": "unique-resource-identifier",
  "resource_type": "virtual_server",
  "provider": "ibm_cloud",
  "region": "us-south",
  "configuration": {
    "name": "my-instance",
    "status": "running",
    "public_access": true,
    "encryption_enabled": false,
    ...
  },
  "timestamp": "2026-05-13T12:00:00Z",
  "tags": {
    "environment": "production"
  },
  "metadata": {
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

## Logging

Logs are written to both console and file (default: `logs/ibm_cloud_collector.log`).

Log levels can be configured via the `LOG_LEVEL` environment variable:
- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

## Error Handling

The tool includes comprehensive error handling:
- Connection failures are caught and logged
- Individual resource collection errors don't stop the entire process
- Detailed error messages with stack traces in log files
- Graceful handling of missing permissions or unavailable services

## Extending the Collector

### Adding a New Collector

1. Create a new collector in `collectors/` directory:
   ```python
   from collectors.base_collector import BaseCollector
   
   class MyCollector(BaseCollector):
       def collect(self):
           resources = []
           # Your collection logic here
           return resources
   ```

2. Import and use in `main.py`:
   ```python
   from collectors import MyCollector
   
   my_collector = MyCollector(client, region, logger)
   results['my_resource'] = my_collector.collect()
   ```

### Adding New IBM Cloud Services

1. Add service client property in `services/ibm_cloud_client.py`
2. Create corresponding collector in `collectors/`
3. Update `main.py` to include the new collector

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your API key is correct
   - Check that the API key has necessary permissions
   - Ensure account ID matches the API key's account

2. **Connection Timeouts**
   - Check your internet connection
   - Verify the region is correct
   - Try a different IBM Cloud region

3. **Missing Resources**
   - Ensure you have resources in the specified region
   - Check IAM permissions for the API key
   - Review logs for specific error messages

4. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're using Python 3.8 or higher

## Security Best Practices

- Never commit `.env` file to version control
- Use API keys with minimal required permissions
- Rotate API keys regularly
- Store credentials securely
- Review collected data before sharing

## Performance Considerations

- Collection time depends on the number of resources
- Large accounts may take several minutes
- Consider running during off-peak hours for large collections
- Use appropriate log levels to reduce I/O overhead

## Future Enhancements

Potential areas for extension:
- Compliance evaluation modules
- Resource comparison and drift detection
- Automated remediation suggestions
- Integration with CI/CD pipelines
- Support for multiple regions in single run
- Export to other formats (CSV, Excel, etc.)
- Real-time monitoring and alerting

## License

This project is provided as-is for educational and operational purposes.

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review error messages in console output
3. Verify environment configuration
4. Consult IBM Cloud documentation for service-specific issues

## Contributing

To contribute:
1. Follow the existing code structure
2. Add appropriate error handling
3. Include logging statements
4. Update documentation
5. Test with various IBM Cloud configurations

## Acknowledgments

Built using official IBM Cloud SDKs:
- ibm-cloud-sdk-core
- ibm-cos-sdk
- ibm-platform-services
- ibm-vpc