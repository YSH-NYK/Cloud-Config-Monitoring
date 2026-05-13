"""Virtual Server Instance collector for IBM Cloud."""

import logging
from typing import List, Dict, Any, Optional
from collectors.base_collector import BaseCollector
from services.ibm_cloud_client import IBMCloudClient


class VSICollector(BaseCollector):
    """Collector for IBM Cloud Virtual Server Instance configurations."""
    
    def __init__(
        self,
        client: IBMCloudClient,
        region: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize VSI collector.
        
        Args:
            client: IBM Cloud client instance
            region: IBM Cloud region
            logger: Logger instance
        """
        super().__init__(client, region, logger)
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect Virtual Server Instance configurations.
        
        Returns:
            List of normalized VSI configurations
        """
        resources = []
        
        try:
            self.logger.info("Collecting Virtual Server Instances...")
            
            response = self.client.vpc.list_instances()
            instances = response.get_result().get('instances', [])
            
            self.logger.info(f"Found {len(instances)} virtual server instances")
            
            for instance in instances:
                try:
                    # Get network interfaces
                    network_interfaces = []
                    for nic in instance.get('network_interfaces', []):
                        network_interfaces.append({
                            'id': nic.get('id'),
                            'name': nic.get('name'),
                            'primary_ipv4_address': nic.get('primary_ipv4_address'),
                            'subnet': nic.get('subnet', {}).get('id'),
                            'security_groups': [sg.get('id') for sg in nic.get('security_groups', [])]
                        })
                    
                    # Get volume attachments
                    volume_attachments = []
                    for vol in instance.get('volume_attachments', []):
                        volume_attachments.append({
                            'id': vol.get('id'),
                            'name': vol.get('name'),
                            'volume_id': vol.get('volume', {}).get('id'),
                            'device': vol.get('device', {}).get('id') if vol.get('device') else None
                        })
                    
                    # Check for public access
                    public_access = False
                    for nic in network_interfaces:
                        if nic.get('primary_ipv4_address'):
                            # Check if instance has floating IP
                            try:
                                fip_response = self.client.vpc.list_instance_network_interface_floating_ips(
                                    instance_id=instance.get('id'),
                                    network_interface_id=nic.get('id')
                                )
                                if fip_response.get_result().get('floating_ips'):
                                    public_access = True
                                    break
                            except Exception:
                                pass
                    
                    config = {
                        'name': instance.get('name'),
                        'status': instance.get('status'),
                        'vpc': instance.get('vpc', {}).get('id'),
                        'zone': instance.get('zone', {}).get('name'),
                        'profile': instance.get('profile', {}).get('name'),
                        'image': instance.get('image', {}).get('id'),
                        'vcpu': instance.get('vcpu', {}).get('count'),
                        'memory': instance.get('memory'),
                        'bandwidth': instance.get('bandwidth'),
                        'boot_volume': instance.get('boot_volume_attachment', {}).get('volume', {}).get('id'),
                        'network_interfaces': network_interfaces,
                        'volume_attachments': volume_attachments,
                        'public_access': public_access,
                        'resource_group': instance.get('resource_group', {}).get('id'),
                        'created_at': instance.get('created_at'),
                        'crn': instance.get('crn')
                    }
                    
                    normalized = self.normalize(
                        resource_id=instance.get('id'),
                        resource_type='virtual_server',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing instance {instance.get('id')}")
            
            self.logger.info(f"Successfully collected {len(resources)} VSI configurations")
            
        except Exception as e:
            self.handle_error(e, "collecting VSI configurations")
        
        return resources


