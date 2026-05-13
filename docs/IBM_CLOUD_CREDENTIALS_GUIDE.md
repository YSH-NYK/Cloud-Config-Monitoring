# IBM Cloud Credentials Guide

This guide explains how to obtain all the required credentials for the IBM Cloud Configuration Collector.

## Table of Contents
1. [IBM Cloud API Key](#ibm-cloud-api-key)
2. [IBM Cloud Account ID](#ibm-cloud-account-id)
3. [Cloud Object Storage Credentials](#cloud-object-storage-credentials)
4. [Region Selection](#region-selection)

---

## IBM Cloud API Key

The API key is used to authenticate with IBM Cloud services.

### Steps to Get API Key:

1. **Log in to IBM Cloud Console**
   - Go to https://cloud.ibm.com
   - Sign in with your credentials

2. **Navigate to API Keys**
   - Click on **Manage** in the top menu
   - Select **Access (IAM)**
   - Click on **API keys** in the left sidebar

3. **Create a New API Key**
   - Click **Create an IBM Cloud API key** button
   - Enter a name (e.g., "config-collector-key")
   - Add a description (optional)
   - Click **Create**

4. **Copy and Save the API Key**
   - **IMPORTANT**: Copy the API key immediately - you won't be able to see it again!
   - Store it securely
   - Paste it into your `.env` file as `IBM_CLOUD_API_KEY`

### Required Permissions:
Your API key needs the following permissions:
- **Viewer** role on VPC Infrastructure Services
- **Viewer** role on IAM Identity Service
- **Viewer** role on IAM Access Groups Service
- **Reader** role on Cloud Object Storage (if collecting COS data)

---

## IBM Cloud Account ID

The Account ID identifies your IBM Cloud account.

### Steps to Get Account ID:

1. **Log in to IBM Cloud Console**
   - Go to https://cloud.ibm.com

2. **Navigate to Account Settings**
   - Click on **Manage** in the top menu
   - Select **Account**

3. **Copy Account ID**
   - You'll see your **Account ID** displayed on the page
   - It's a long alphanumeric string (e.g., `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)
   - Copy this value
   - Paste it into your `.env` file as `IBM_CLOUD_ACCOUNT_ID`

---

## Cloud Object Storage Credentials

These credentials are **optional** and only needed if you want to collect Cloud Object Storage configurations.

### Prerequisites:
- You must have a Cloud Object Storage instance created in your IBM Cloud account
- If you don't have one, you can skip these credentials (the collector will skip COS collection)

### Steps to Get COS Credentials:

#### 1. Find Your COS Instance

1. **Navigate to Resource List**
   - In IBM Cloud Console, click **Navigation Menu** (☰)
   - Select **Resource list**

2. **Locate Your COS Instance**
   - Expand the **Storage** section
   - Find your Cloud Object Storage instance
   - Click on the instance name

#### 2. Get COS Instance CRN

1. **View Instance Details**
   - On the COS instance page, you'll see the instance details
   - Look for **CRN** (Cloud Resource Name)
   - It looks like: `crn:v1:bluemix:public:cloud-object-storage:global:a/xxxxx:yyyyy::`
   - Copy this entire CRN
   - Paste it into your `.env` file as `IBM_COS_INSTANCE_CRN`

#### 3. Create Service Credentials

1. **Navigate to Service Credentials**
   - In your COS instance page, click **Service credentials** in the left menu

2. **Create New Credentials** (if you don't have any)
   - Click **New credential** button
   - Enter a name (e.g., "config-collector-credentials")
   - Select **Writer** role (or **Reader** if you only need read access)
   - Click **Add**

3. **View Credentials**
   - Click on the credential name or **View credentials** button
   - You'll see a JSON object with various fields

4. **Extract Required Values**
   
   From the JSON credentials, copy these values:
   
   - **API Key**: Look for `"apikey"` field
     ```json
     "apikey": "your-cos-api-key-here"
     ```
     Copy this value to `.env` as `IBM_COS_API_KEY`
   
   - **Instance CRN**: Look for `"resource_instance_id"` field
     ```json
     "resource_instance_id": "crn:v1:bluemix:public:cloud-object-storage:global:a/xxxxx:yyyyy::"
     ```
     This should match the CRN you copied earlier

#### 4. Determine COS Endpoint

The endpoint depends on your region and whether you want public or private access.

**Format**: `https://s3.{region}.cloud-object-storage.appdomain.cloud`

**Common Endpoints**:
- **US South**: `https://s3.us-south.cloud-object-storage.appdomain.cloud`
- **US East**: `https://s3.us-east.cloud-object-storage.appdomain.cloud`
- **EU Germany**: `https://s3.eu-de.cloud-object-storage.appdomain.cloud`
- **EU Great Britain**: `https://s3.eu-gb.cloud-object-storage.appdomain.cloud`
- **Japan Tokyo**: `https://s3.jp-tok.cloud-object-storage.appdomain.cloud`
- **Australia Sydney**: `https://s3.au-syd.cloud-object-storage.appdomain.cloud`

**To find your specific endpoint**:
1. In your COS instance, click **Buckets** in the left menu
2. Click on any bucket
3. Click **Configuration** tab
4. Look for **Public endpoint** or **Private endpoint**
5. Copy the endpoint URL
6. Paste it into your `.env` file as `IBM_COS_ENDPOINT`

**Note**: Use the **public endpoint** unless you're running the collector from within IBM Cloud infrastructure.

---

## Region Selection

Choose the IBM Cloud region where your resources are located.

### Available Regions:

| Region Code | Location | Description |
|------------|----------|-------------|
| `us-south` | Dallas, USA | US South (Dallas) |
| `us-east` | Washington DC, USA | US East |
| `eu-gb` | London, UK | United Kingdom |
| `eu-de` | Frankfurt, Germany | Germany |
| `jp-tok` | Tokyo, Japan | Japan |
| `jp-osa` | Osaka, Japan | Japan (Osaka) |
| `au-syd` | Sydney, Australia | Australia |
| `ca-tor` | Toronto, Canada | Canada |
| `br-sao` | São Paulo, Brazil | Brazil |

### How to Choose:
1. Determine where your resources are deployed
2. Use the corresponding region code
3. Set it in your `.env` file as `IBM_CLOUD_REGION`

**Note**: The collector will only fetch resources from the specified region. To collect from multiple regions, you'll need to run the collector multiple times with different region settings.

---

## Complete .env File Example

Here's what your `.env` file should look like with all values filled in:

```env
# Required: IBM Cloud API Key
IBM_CLOUD_API_KEY=AbCdEfGhIjKlMnOpQrStUvWxYz1234567890

# Required: IBM Cloud Account ID
IBM_CLOUD_ACCOUNT_ID=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Required: IBM Cloud Region
IBM_CLOUD_REGION=us-south

# Optional: Cloud Object Storage Configuration
IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
IBM_COS_API_KEY=XyZ9876543210AbCdEfGhIjKlMnOpQrSt
IBM_COS_INSTANCE_CRN=crn:v1:bluemix:public:cloud-object-storage:global:a/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:12345678-1234-1234-1234-123456789012::

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/ibm_cloud_collector.log

# Optional: Output Configuration
OUTPUT_DIR=output
```

---

## Troubleshooting

### "Authentication failed" Error
- Verify your API key is correct (no extra spaces)
- Check that the API key hasn't expired
- Ensure the API key has the required permissions

### "Account not found" Error
- Double-check your Account ID
- Ensure you're using the correct IBM Cloud account

### "COS credentials invalid" Error
- Verify the COS API key is correct
- Check that the COS Instance CRN matches your instance
- Ensure the endpoint URL is correct for your region

### "No resources found" Error
- Verify you have resources in the specified region
- Check that your API key has permission to view the resources
- Try a different region if your resources are elsewhere

---

## Security Best Practices

1. **Never commit credentials to version control**
   - The `.env` file is in `.gitignore` by default
   - Never share your `.env` file

2. **Use least privilege**
   - Grant only the minimum required permissions
   - Use **Viewer/Reader** roles when possible

3. **Rotate credentials regularly**
   - Create new API keys periodically
   - Delete old, unused keys

4. **Store credentials securely**
   - Use a password manager for long-term storage
   - Don't store credentials in plain text files outside the project

5. **Monitor API key usage**
   - Regularly check IBM Cloud audit logs
   - Look for unexpected API calls

---

## Additional Resources

- [IBM Cloud API Keys Documentation](https://cloud.ibm.com/docs/account?topic=account-userapikey)
- [IBM Cloud Object Storage Documentation](https://cloud.ibm.com/docs/cloud-object-storage)
- [IBM Cloud IAM Documentation](https://cloud.ibm.com/docs/account?topic=account-iamoverview)
- [IBM Cloud VPC Documentation](https://cloud.ibm.com/docs/vpc)

---

## Need Help?

If you're still having trouble obtaining credentials:

1. Check the IBM Cloud Console documentation
2. Contact your IBM Cloud account administrator
3. Review the IBM Cloud support resources
4. Check the project's main README.md for additional troubleshooting tips