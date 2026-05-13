"""VPC collector for IBM Cloud."""

import logging
from typing import List, Dict, Any, Optional
from collectors.base_collector import BaseCollector
from services.ibm_cloud_client import IBMCloudClient


class VPCCollector(BaseCollector):
    """Collector for IBM Cloud VPC and networking configurations."""
    
    def __init__(
        self,
        client: IBMCloudClient,
        region: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize VPC collector.
        
        Args:
            client: IBM Cloud client instance
            region: IBM Cloud region
            logger: Logger instance
        """
        super().__init__(client, region, logger)
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect VPC and networking configurations.
        
        Returns:
            List of normalized VPC configurations
        """
        resources = []
        
        try:
            self.logger.info("Collecting VPC configurations...")
            
            # Collect VPCs
            resources.extend(self._collect_vpcs())
            
            # Collect subnets
            resources.extend(self._collect_subnets())
            
            # Collect public gateways
            resources.extend(self._collect_public_gateways())
            
            # Collect floating IPs
            resources.extend(self._collect_floating_ips())
            
            # Collect load balancers
            resources.extend(self._collect_load_balancers())
            
            self.logger.info(f"Successfully collected {len(resources)} VPC configurations")
            
        except Exception as e:
            self.handle_error(e, "collecting VPC configurations")
        
        return resources
    
    def _collect_vpcs(self) -> List[Dict[str, Any]]:
        """Collect VPCs."""
        resources = []
        
        try:
            self.logger.info("Collecting VPCs...")
            
            response = self.client.vpc.list_vpcs()
            vpcs = response.get_result().get('vpcs', [])
            
            self.logger.info(f"Found {len(vpcs)} VPCs")
            
            for vpc in vpcs:
                try:
                    config = {
                        'name': vpc.get('name'),
                        'status': vpc.get('status'),
                        'classic_access': vpc.get('classic_access', False),
                        'default_network_acl': vpc.get('default_network_acl', {}).get('id'),
                        'default_routing_table': vpc.get('default_routing_table', {}).get('id'),
                        'default_security_group': vpc.get('default_security_group', {}).get('id'),
                        'resource_group': vpc.get('resource_group', {}).get('id'),
                        'created_at': vpc.get('created_at'),
                        'crn': vpc.get('crn')
                    }
                    
                    normalized = self.normalize(
                        resource_id=vpc.get('id'),
                        resource_type='vpc',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing VPC {vpc.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting VPCs")
        
        return resources
    
    def _collect_subnets(self) -> List[Dict[str, Any]]:
        """Collect subnets."""
        resources = []
        
        try:
            self.logger.info("Collecting subnets...")
            
            response = self.client.vpc.list_subnets()
            subnets = response.get_result().get('subnets', [])
            
            self.logger.info(f"Found {len(subnets)} subnets")
            
            for subnet in subnets:
                try:
                    config = {
                        'name': subnet.get('name'),
                        'status': subnet.get('status'),
                        'ipv4_cidr_block': subnet.get('ipv4_cidr_block'),
                        'available_ipv4_address_count': subnet.get('available_ipv4_address_count'),
                        'total_ipv4_address_count': subnet.get('total_ipv4_address_count'),
                        'vpc': subnet.get('vpc', {}).get('id'),
                        'zone': subnet.get('zone', {}).get('name'),
                        'network_acl': subnet.get('network_acl', {}).get('id'),
                        'public_gateway': subnet.get('public_gateway', {}).get('id') if subnet.get('public_gateway') else None,
                        'resource_group': subnet.get('resource_group', {}).get('id'),
                        'created_at': subnet.get('created_at')
                    }
                    
                    normalized = self.normalize(
                        resource_id=subnet.get('id'),
                        resource_type='subnet',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing subnet {subnet.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting subnets")
        
        return resources
    
    def _collect_public_gateways(self) -> List[Dict[str, Any]]:
        """Collect public gateways."""
        resources = []
        
        try:
            self.logger.info("Collecting public gateways...")
            
            response = self.client.vpc.list_public_gateways()
            gateways = response.get_result().get('public_gateways', [])
            
            self.logger.info(f"Found {len(gateways)} public gateways")
            
            for gateway in gateways:
                try:
                    config = {
                        'name': gateway.get('name'),
                        'status': gateway.get('status'),
                        'vpc': gateway.get('vpc', {}).get('id'),
                        'zone': gateway.get('zone', {}).get('name'),
                        'floating_ip': gateway.get('floating_ip', {}).get('address'),
                        'resource_group': gateway.get('resource_group', {}).get('id'),
                        'created_at': gateway.get('created_at')
                    }
                    
                    normalized = self.normalize(
                        resource_id=gateway.get('id'),
                        resource_type='public_gateway',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing public gateway {gateway.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting public gateways")
        
        return resources
    
    def _collect_floating_ips(self) -> List[Dict[str, Any]]:
        """Collect floating IPs."""
        resources = []
        
        try:
            self.logger.info("Collecting floating IPs...")
            
            response = self.client.vpc.list_floating_ips()
            floating_ips = response.get_result().get('floating_ips', [])
            
            self.logger.info(f"Found {len(floating_ips)} floating IPs")
            
            for fip in floating_ips:
                try:
                    config = {
                        'name': fip.get('name'),
                        'address': fip.get('address'),
                        'status': fip.get('status'),
                        'zone': fip.get('zone', {}).get('name'),
                        'target': fip.get('target', {}).get('id') if fip.get('target') else None,
                        'resource_group': fip.get('resource_group', {}).get('id'),
                        'created_at': fip.get('created_at')
                    }
                    
                    normalized = self.normalize(
                        resource_id=fip.get('id'),
                        resource_type='floating_ip',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing floating IP {fip.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting floating IPs")
        
        return resources
    
    def _collect_load_balancers(self) -> List[Dict[str, Any]]:
        """Collect load balancers."""
        resources = []
        
        try:
            self.logger.info("Collecting load balancers...")
            
            response = self.client.vpc.list_load_balancers()
            load_balancers = response.get_result().get('load_balancers', [])
            
            self.logger.info(f"Found {len(load_balancers)} load balancers")
            
            for lb in load_balancers:
                try:
                    config = {
                        'name': lb.get('name'),
                        'hostname': lb.get('hostname'),
                        'is_public': lb.get('is_public', False),
                        'operating_status': lb.get('operating_status'),
                        'provisioning_status': lb.get('provisioning_status'),
                        'subnets': [s.get('id') for s in lb.get('subnets', [])],
                        'listeners': [l.get('id') for l in lb.get('listeners', [])],
                        'pools': [p.get('id') for p in lb.get('pools', [])],
                        'resource_group': lb.get('resource_group', {}).get('id'),
                        'created_at': lb.get('created_at')
                    }
                    
                    normalized = self.normalize(
                        resource_id=lb.get('id'),
                        resource_type='load_balancer',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing load balancer {lb.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting load balancers")
        
        return resources


