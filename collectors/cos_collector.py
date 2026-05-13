"""Cloud Object Storage collector for IBM Cloud."""

import logging
from typing import List, Dict, Any, Optional
from collectors.base_collector import BaseCollector
from services.ibm_cloud_client import IBMCloudClient


class COSCollector(BaseCollector):
    """Collector for IBM Cloud Object Storage configurations."""
    
    def __init__(
        self,
        client: IBMCloudClient,
        region: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize COS collector.
        
        Args:
            client: IBM Cloud client instance
            region: IBM Cloud region
            logger: Logger instance
        """
        super().__init__(client, region, logger)
        self.resource_type = "cloud_object_storage"
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect Cloud Object Storage configurations.
        
        Returns:
            List of normalized COS bucket configurations
        """
        resources = []
        
        try:
            if not self.client.cos:
                self.logger.warning("COS client not configured, skipping COS collection")
                return resources
            
            self.logger.info("Collecting Cloud Object Storage configurations...")
            
            # List all buckets
            response = self.client.cos.list_buckets()
            buckets = response.get('Buckets', [])
            
            self.logger.info(f"Found {len(buckets)} COS buckets")
            
            for bucket in buckets:
                try:
                    bucket_name = bucket['Name']
                    
                    # Get bucket configuration details
                    bucket_config = self._get_bucket_configuration(bucket_name)
                    
                    # Normalize and add to resources
                    normalized = self.normalize(
                        resource_id=bucket_name,
                        resource_type=self.resource_type,
                        configuration=bucket_config,
                        metadata={
                            'creation_date': bucket.get('CreationDate', '').isoformat() if bucket.get('CreationDate') else None
                        }
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"collecting bucket {bucket.get('Name', 'unknown')}")
            
            self.logger.info(f"Successfully collected {len(resources)} COS configurations")
            
        except Exception as e:
            self.handle_error(e, "collecting COS configurations")
        
        return resources
    
    def _get_bucket_configuration(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get detailed configuration for a bucket.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            Dictionary with bucket configuration details
        """
        config = {
            'bucket_name': bucket_name,
            'public_access': False,
            'encryption_enabled': False,
            'versioning_enabled': False,
            'lifecycle_rules': [],
            'cors_rules': []
        }
        
        try:
            # Check bucket ACL for public access
            try:
                acl = self.client.cos.get_bucket_acl(Bucket=bucket_name)
                grants = acl.get('Grants', [])
                for grant in grants:
                    grantee = grant.get('Grantee', {})
                    if grantee.get('Type') == 'Group' and 'AllUsers' in grantee.get('URI', ''):
                        config['public_access'] = True
                        break
            except Exception:
                pass
            
            # Check encryption
            try:
                encryption = self.client.cos.get_bucket_encryption(Bucket=bucket_name)
                if encryption.get('ServerSideEncryptionConfiguration'):
                    config['encryption_enabled'] = True
            except Exception:
                pass
            
            # Check versioning
            try:
                versioning = self.client.cos.get_bucket_versioning(Bucket=bucket_name)
                config['versioning_enabled'] = versioning.get('Status') == 'Enabled'
            except Exception:
                pass
            
            # Check lifecycle configuration
            try:
                lifecycle = self.client.cos.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                config['lifecycle_rules'] = lifecycle.get('Rules', [])
            except Exception:
                pass
            
            # Check CORS configuration
            try:
                cors = self.client.cos.get_bucket_cors(Bucket=bucket_name)
                config['cors_rules'] = cors.get('CORSRules', [])
            except Exception:
                pass
                
        except Exception as e:
            self.logger.warning(f"Error getting configuration for bucket {bucket_name}: {str(e)}")
        
        return config


