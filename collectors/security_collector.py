"""Security group and firewall rules collector for IBM Cloud."""

import logging
from typing import List, Dict, Any, Optional
from collectors.base_collector import BaseCollector
from services.ibm_cloud_client import IBMCloudClient


class SecurityCollector(BaseCollector):
    """Collector for IBM Cloud security groups and firewall rules."""
    
    def __init__(
        self,
        client: IBMCloudClient,
        region: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Security collector.
        
        Args:
            client: IBM Cloud client instance
            region: IBM Cloud region
            logger: Logger instance
        """
        super().__init__(client, region, logger)
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect security group and firewall configurations.
        
        Returns:
            List of normalized security configurations
        """
        resources = []
        
        try:
            self.logger.info("Collecting security configurations...")
            
            # Collect security groups
            resources.extend(self._collect_security_groups())
            
            # Collect network ACLs
            resources.extend(self._collect_network_acls())
            
            self.logger.info(f"Successfully collected {len(resources)} security configurations")
            
        except Exception as e:
            self.handle_error(e, "collecting security configurations")
        
        return resources
    
    def _collect_security_groups(self) -> List[Dict[str, Any]]:
        """Collect security groups and their rules."""
        resources = []
        
        try:
            self.logger.info("Collecting security groups...")
            
            response = self.client.vpc.list_security_groups()
            security_groups = response.get_result().get('security_groups', [])
            
            self.logger.info(f"Found {len(security_groups)} security groups")
            
            for sg in security_groups:
                try:
                    # Process inbound rules
                    inbound_rules = []
                    for rule in sg.get('rules', []):
                        if rule.get('direction') == 'inbound':
                            inbound_rules.append(self._format_security_rule(rule))
                    
                    # Process outbound rules
                    outbound_rules = []
                    for rule in sg.get('rules', []):
                        if rule.get('direction') == 'outbound':
                            outbound_rules.append(self._format_security_rule(rule))
                    
                    # Check for overly permissive rules
                    has_permissive_rules = self._check_permissive_rules(sg.get('rules', []))
                    
                    config = {
                        'name': sg.get('name'),
                        'vpc': sg.get('vpc', {}).get('id'),
                        'resource_group': sg.get('resource_group', {}).get('id'),
                        'inbound_rules': inbound_rules,
                        'outbound_rules': outbound_rules,
                        'inbound_rule_count': len(inbound_rules),
                        'outbound_rule_count': len(outbound_rules),
                        'has_permissive_rules': has_permissive_rules,
                        'created_at': sg.get('created_at'),
                        'crn': sg.get('crn')
                    }
                    
                    normalized = self.normalize(
                        resource_id=sg.get('id'),
                        resource_type='security_group',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing security group {sg.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting security groups")
        
        return resources
    
    def _collect_network_acls(self) -> List[Dict[str, Any]]:
        """Collect network ACLs and their rules."""
        resources = []
        
        try:
            self.logger.info("Collecting network ACLs...")
            
            response = self.client.vpc.list_network_acls()
            network_acls = response.get_result().get('network_acls', [])
            
            self.logger.info(f"Found {len(network_acls)} network ACLs")
            
            for acl in network_acls:
                try:
                    # Process inbound rules
                    inbound_rules = []
                    for rule in acl.get('rules', []):
                        if rule.get('direction') == 'inbound':
                            inbound_rules.append(self._format_acl_rule(rule))
                    
                    # Process outbound rules
                    outbound_rules = []
                    for rule in acl.get('rules', []):
                        if rule.get('direction') == 'outbound':
                            outbound_rules.append(self._format_acl_rule(rule))
                    
                    config = {
                        'name': acl.get('name'),
                        'vpc': acl.get('vpc', {}).get('id'),
                        'resource_group': acl.get('resource_group', {}).get('id'),
                        'inbound_rules': inbound_rules,
                        'outbound_rules': outbound_rules,
                        'inbound_rule_count': len(inbound_rules),
                        'outbound_rule_count': len(outbound_rules),
                        'subnets': [s.get('id') for s in acl.get('subnets', [])],
                        'created_at': acl.get('created_at'),
                        'crn': acl.get('crn')
                    }
                    
                    normalized = self.normalize(
                        resource_id=acl.get('id'),
                        resource_type='network_acl',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing network ACL {acl.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting network ACLs")
        
        return resources
    
    def _format_security_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Format security group rule."""
        formatted = {
            'id': rule.get('id'),
            'direction': rule.get('direction'),
            'protocol': rule.get('protocol'),
            'ip_version': rule.get('ip_version')
        }
        
        # Add remote information
        remote = rule.get('remote', {})
        if isinstance(remote, dict):
            if remote.get('cidr_block'):
                formatted['remote'] = remote.get('cidr_block')
            elif remote.get('address'):
                formatted['remote'] = remote.get('address')
            else:
                formatted['remote'] = remote.get('id', 'any')
        else:
            formatted['remote'] = str(remote)
        
        # Add port information
        if rule.get('port_min'):
            formatted['port_min'] = rule.get('port_min')
        if rule.get('port_max'):
            formatted['port_max'] = rule.get('port_max')
        
        return formatted
    
    def _format_acl_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Format network ACL rule."""
        formatted = {
            'id': rule.get('id'),
            'name': rule.get('name'),
            'action': rule.get('action'),
            'direction': rule.get('direction'),
            'protocol': rule.get('protocol'),
            'source': rule.get('source'),
            'destination': rule.get('destination')
        }
        
        # Add port information
        if rule.get('source_port_min'):
            formatted['source_port_min'] = rule.get('source_port_min')
        if rule.get('source_port_max'):
            formatted['source_port_max'] = rule.get('source_port_max')
        if rule.get('destination_port_min'):
            formatted['destination_port_min'] = rule.get('destination_port_min')
        if rule.get('destination_port_max'):
            formatted['destination_port_max'] = rule.get('destination_port_max')
        
        return formatted
    
    def _check_permissive_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """Check if security group has overly permissive rules."""
        for rule in rules:
            remote = rule.get('remote', {})
            
            # Check for 0.0.0.0/0 or ::/0
            if isinstance(remote, dict):
                cidr = remote.get('cidr_block', '')
                if cidr in ['0.0.0.0/0', '::/0']:
                    return True
            elif isinstance(remote, str):
                if remote in ['0.0.0.0/0', '::/0']:
                    return True
        
        return False

# Made with Bob
