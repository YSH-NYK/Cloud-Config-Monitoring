"""Settings module for loading environment variables and configuration."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Configuration settings for IBM Cloud collector."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # IBM Cloud credentials
        self.api_key: str = os.getenv('IBM_CLOUD_API_KEY', '')
        self.account_id: str = os.getenv('IBM_CLOUD_ACCOUNT_ID', '')
        self.region: str = os.getenv('IBM_CLOUD_REGION', 'us-south')
        
        # IBM Cloud Object Storage
        self.cos_endpoint: str = os.getenv('IBM_COS_ENDPOINT', '')
        self.cos_api_key: str = os.getenv('IBM_COS_API_KEY', '')
        self.cos_instance_crn: str = os.getenv('IBM_COS_INSTANCE_CRN', '')
        
        # VPC Configuration
        self.vpc_generation: int = int(os.getenv('IBM_VPC_GENERATION', '2'))
        
        # Logging
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file: str = os.getenv('LOG_FILE', 'logs/ibm_cloud_collector.log')
        
        # Output
        self.output_dir: str = os.getenv('OUTPUT_DIR', 'output')
        
    def validate(self) -> bool:
        """
        Validate that required settings are present.
        
        Returns:
            bool: True if all required settings are present, False otherwise.
        """
        required_fields = [
            ('IBM_CLOUD_API_KEY', self.api_key),
            ('IBM_CLOUD_ACCOUNT_ID', self.account_id),
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            print(f"Missing required environment variables: {', '.join(missing_fields)}")
            return False
        
        return True
    
    def __repr__(self) -> str:
        """Return string representation of settings (without sensitive data)."""
        return (
            f"Settings(region={self.region}, "
            f"vpc_generation={self.vpc_generation}, "
            f"log_level={self.log_level}, "
            f"output_dir={self.output_dir})"
        )


# Global settings instance
settings = Settings()


