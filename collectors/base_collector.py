"""Base collector class for IBM Cloud resources."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from services.ibm_cloud_client import IBMCloudClient
from utils.json_handler import normalize_resource


class BaseCollector(ABC):
    """Abstract base class for resource collectors."""
    
    def __init__(
        self,
        client: IBMCloudClient,
        region: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize base collector.
        
        Args:
            client: IBM Cloud client instance
            region: IBM Cloud region
            logger: Logger instance
        """
        self.client = client
        self.region = region
        self.logger = logger or logging.getLogger(__name__)
        self.provider = "ibm_cloud"
    
    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect resources from IBM Cloud.
        
        Returns:
            List of normalized resource dictionaries
        """
        pass
    
    def normalize(
        self,
        resource_id: str,
        resource_type: str,
        configuration: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Normalize resource data using the utility function.
        
        Args:
            resource_id: Unique identifier for the resource
            resource_type: Type of resource
            configuration: Resource-specific configuration
            tags: Optional resource tags
            metadata: Optional additional metadata
            
        Returns:
            Normalized resource dictionary
        """
        return normalize_resource(
            resource_id=resource_id,
            resource_type=resource_type,
            provider=self.provider,
            region=self.region,
            configuration=configuration,
            tags=tags,
            metadata=metadata
        )
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle and log errors consistently.
        
        Args:
            error: Exception that occurred
            context: Additional context about where the error occurred
        """
        error_msg = f"Error in {self.__class__.__name__}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        self.logger.error(error_msg, exc_info=True)


