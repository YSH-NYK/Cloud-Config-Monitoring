"""IBM Cloud client for managing API connections."""

import logging
from typing import Optional
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services import IamIdentityV1, IamAccessGroupsV2, IamPolicyManagementV1
from ibm_vpc import VpcV1
import ibm_boto3
from ibm_botocore.client import Config


class IBMCloudClient:
    """Client for IBM Cloud services."""
    
    def __init__(
        self,
        api_key: str,
        region: str = 'us-south',
        cos_endpoint: Optional[str] = None,
        cos_api_key: Optional[str] = None,
        cos_instance_crn: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize IBM Cloud client.
        
        Args:
            api_key: IBM Cloud API key
            region: IBM Cloud region
            cos_endpoint: Cloud Object Storage endpoint
            cos_api_key: Cloud Object Storage API key
            cos_instance_crn: Cloud Object Storage instance CRN
            logger: Logger instance
        """
        self.api_key = api_key
        self.region = region
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize authenticator
        self.authenticator = IAMAuthenticator(api_key)
        
        # Initialize service clients
        self._iam_identity_client: Optional[IamIdentityV1] = None
        self._iam_access_groups_client: Optional[IamAccessGroupsV2] = None
        self._iam_policy_client: Optional[IamPolicyManagementV1] = None
        self._vpc_client: Optional[VpcV1] = None
        self._cos_client = None
        
        # Store COS credentials
        self.cos_endpoint = cos_endpoint
        self.cos_api_key = cos_api_key
        self.cos_instance_crn = cos_instance_crn
        
        self.logger.info(f"IBM Cloud client initialized for region: {region}")
    
    @property
    def iam_identity(self) -> IamIdentityV1:
        """Get IAM Identity service client."""
        if not self._iam_identity_client:
            self._iam_identity_client = IamIdentityV1(authenticator=self.authenticator)
            self._iam_identity_client.set_service_url(
                f'https://iam.cloud.ibm.com'
            )
            self.logger.debug("IAM Identity client initialized")
        return self._iam_identity_client
    
    @property
    def iam_access_groups(self) -> IamAccessGroupsV2:
        """Get IAM Access Groups service client."""
        if not self._iam_access_groups_client:
            self._iam_access_groups_client = IamAccessGroupsV2(
                authenticator=self.authenticator
            )
            self._iam_access_groups_client.set_service_url(
                f'https://iam.cloud.ibm.com'
            )
            self.logger.debug("IAM Access Groups client initialized")
        return self._iam_access_groups_client
    
    @property
    def iam_policy(self) -> IamPolicyManagementV1:
        """Get IAM Policy Management service client."""
        if not self._iam_policy_client:
            self._iam_policy_client = IamPolicyManagementV1(
                authenticator=self.authenticator
            )
            self._iam_policy_client.set_service_url(
                f'https://iam.cloud.ibm.com'
            )
            self.logger.debug("IAM Policy Management client initialized")
        return self._iam_policy_client
    
    @property
    def vpc(self) -> VpcV1:
        """Get VPC service client."""
        if not self._vpc_client:
            self._vpc_client = VpcV1(
                version='2024-01-01',
                authenticator=self.authenticator
            )
            # Set service URL based on region
            self._vpc_client.set_service_url(
                f'https://{self.region}.iaas.cloud.ibm.com/v1'
            )
            self.logger.debug(f"VPC client initialized for region: {self.region}")
        return self._vpc_client
    
    @property
    def cos(self):
        """Get Cloud Object Storage client."""
        if not self._cos_client and self.cos_endpoint and self.cos_api_key:
            self._cos_client = ibm_boto3.client(
                's3',
                ibm_api_key_id=self.cos_api_key,
                ibm_service_instance_id=self.cos_instance_crn,
                config=Config(signature_version='oauth'),
                endpoint_url=self.cos_endpoint
            )
            self.logger.debug("Cloud Object Storage client initialized")
        return self._cos_client
    
    def test_connection(self) -> bool:
        """
        Test connection to IBM Cloud.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to list VPCs as a connection test
            response = self.vpc.list_vpcs()
            self.logger.info("Connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

# Made with Bob
