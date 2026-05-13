#!/usr/bin/env python3
"""
IBM Cloud Configuration Collector

This script collects infrastructure configuration details from IBM Cloud
and stores them as structured JSON files.
"""

import sys
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from config import Settings
from services import IBMCloudClient
from collectors import (
    COSCollector,
    IAMCollector,
    VPCCollector,
    VSICollector,
    SecurityCollector
)
from utils import setup_logger, save_json


class IBMCloudConfigCollector:
    """Main collector orchestrator for IBM Cloud configurations."""
    
    def __init__(self):
        """Initialize the collector."""
        # Load settings
        self.settings = Settings()
        
        # Setup logger
        self.logger = setup_logger(
            log_level=self.settings.log_level,
            log_file=self.settings.log_file
        )
        
        # Validate settings
        if not self.settings.validate():
            self.logger.error("Invalid configuration. Please check your .env file.")
            sys.exit(1)
        
        # Initialize IBM Cloud client
        self.client = IBMCloudClient(
            api_key=self.settings.api_key,
            region=self.settings.region,
            cos_endpoint=self.settings.cos_endpoint,
            cos_api_key=self.settings.cos_api_key,
            cos_instance_crn=self.settings.cos_instance_crn,
            logger=self.logger
        )
        
        self.logger.info("IBM Cloud Configuration Collector initialized")
    
    def test_connection(self) -> bool:
        """
        Test connection to IBM Cloud.
        
        Returns:
            bool: True if connection is successful
        """
        self.logger.info("Testing connection to IBM Cloud...")
        return self.client.test_connection()
    
    def collect_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect all configurations from IBM Cloud.
        
        Returns:
            Dictionary with collected resources by type
        """
        results = {
            'cos': [],
            'iam': [],
            'vpc': [],
            'vsi': [],
            'security': []
        }
        
        try:
            # Collect Cloud Object Storage configurations
            self.logger.info("=" * 60)
            self.logger.info("Starting Cloud Object Storage collection...")
            cos_collector = COSCollector(
                client=self.client,
                region=self.settings.region,
                logger=self.logger
            )
            results['cos'] = cos_collector.collect()
            
            # Collect IAM configurations
            self.logger.info("=" * 60)
            self.logger.info("Starting IAM collection...")
            iam_collector = IAMCollector(
                client=self.client,
                region=self.settings.region,
                account_id=self.settings.account_id,
                logger=self.logger
            )
            results['iam'] = iam_collector.collect()
            
            # Collect VPC configurations
            self.logger.info("=" * 60)
            self.logger.info("Starting VPC collection...")
            vpc_collector = VPCCollector(
                client=self.client,
                region=self.settings.region,
                logger=self.logger
            )
            results['vpc'] = vpc_collector.collect()
            
            # Collect Virtual Server Instance configurations
            self.logger.info("=" * 60)
            self.logger.info("Starting Virtual Server Instance collection...")
            vsi_collector = VSICollector(
                client=self.client,
                region=self.settings.region,
                logger=self.logger
            )
            results['vsi'] = vsi_collector.collect()
            
            # Collect Security configurations
            self.logger.info("=" * 60)
            self.logger.info("Starting Security configuration collection...")
            security_collector = SecurityCollector(
                client=self.client,
                region=self.settings.region,
                logger=self.logger
            )
            results['security'] = security_collector.collect()
            
        except Exception as e:
            self.logger.error(f"Error during collection: {str(e)}", exc_info=True)
        
        return results
    
    def save_results(self, results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """
        Save collected results to JSON files.
        
        Args:
            results: Dictionary with collected resources
            
        Returns:
            Dictionary with saved file paths
        """
        saved_files = {}
        
        try:
            # Save individual resource type files
            for resource_type, resources in results.items():
                if resources:
                    filename = f"ibm_cloud_{resource_type}"
                    filepath = save_json(
                        data=resources,
                        filename=filename,
                        output_dir=self.settings.output_dir,
                        use_timestamp=True
                    )
                    saved_files[resource_type] = filepath
                    self.logger.info(f"Saved {len(resources)} {resource_type} resources to {filepath}")
            
            # Save combined file with all resources
            all_resources = []
            for resources in results.values():
                all_resources.extend(resources)
            
            if all_resources:
                combined_filepath = save_json(
                    data=all_resources,
                    filename="ibm_cloud_all_resources",
                    output_dir=self.settings.output_dir,
                    use_timestamp=True
                )
                saved_files['all'] = combined_filepath
                self.logger.info(f"Saved {len(all_resources)} total resources to {combined_filepath}")
            
            # Save summary
            summary = {
                'collection_timestamp': datetime.utcnow().isoformat() + 'Z',
                'region': self.settings.region,
                'resource_counts': {
                    resource_type: len(resources)
                    for resource_type, resources in results.items()
                },
                'total_resources': len(all_resources),
                'output_files': saved_files
            }
            
            summary_filepath = save_json(
                data=summary,
                filename="collection_summary",
                output_dir=self.settings.output_dir,
                use_timestamp=True
            )
            saved_files['summary'] = summary_filepath
            self.logger.info(f"Saved collection summary to {summary_filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}", exc_info=True)
        
        return saved_files
    
    def run(self):
        """Run the complete collection process."""
        self.logger.info("=" * 60)
        self.logger.info("IBM Cloud Configuration Collection Started")
        self.logger.info("=" * 60)
        
        start_time = datetime.utcnow()
        
        # Test connection
        if not self.test_connection():
            self.logger.error("Connection test failed. Exiting.")
            sys.exit(1)
        
        # Collect all configurations
        results = self.collect_all()
        
        # Save results
        saved_files = self.save_results(results)
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("Collection Complete!")
        self.logger.info("=" * 60)
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info(f"Total resources collected: {sum(len(r) for r in results.values())}")
        self.logger.info("Resource breakdown:")
        for resource_type, resources in results.items():
            self.logger.info(f"  - {resource_type}: {len(resources)}")
        self.logger.info("\nOutput files:")
        for file_type, filepath in saved_files.items():
            self.logger.info(f"  - {file_type}: {filepath}")
        self.logger.info("=" * 60)


def main():
    """Main entry point."""
    try:
        collector = IBMCloudConfigCollector()
        collector.run()
    except KeyboardInterrupt:
        print("\n\nCollection interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()


