"""IAM collector for IBM Cloud."""

import logging
from typing import List, Dict, Any, Optional
from collectors.base_collector import BaseCollector
from services.ibm_cloud_client import IBMCloudClient


class IAMCollector(BaseCollector):
    """Collector for IBM Cloud IAM users, roles, and access policies."""
    
    def __init__(
        self,
        client: IBMCloudClient,
        region: str,
        account_id: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize IAM collector.
        
        Args:
            client: IBM Cloud client instance
            region: IBM Cloud region
            account_id: IBM Cloud account ID
            logger: Logger instance
        """
        super().__init__(client, region, logger)
        self.account_id = account_id
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect IAM configurations including users, service IDs, access groups, and policies.
        
        Returns:
            List of normalized IAM configurations
        """
        resources = []
        
        try:
            self.logger.info("Collecting IAM configurations...")
            
            # Collect service IDs
            resources.extend(self._collect_service_ids())
            
            # Collect access groups
            resources.extend(self._collect_access_groups())
            
            # Collect policies
            resources.extend(self._collect_policies())
            
            self.logger.info(f"Successfully collected {len(resources)} IAM configurations")
            
        except Exception as e:
            self.handle_error(e, "collecting IAM configurations")
        
        return resources
    
    def _collect_service_ids(self) -> List[Dict[str, Any]]:
        """Collect service IDs."""
        resources = []
        
        try:
            self.logger.info("Collecting service IDs...")
            
            response = self.client.iam_identity.list_service_ids(
                account_id=self.account_id
            )
            
            service_ids = response.get_result().get('serviceids', [])
            self.logger.info(f"Found {len(service_ids)} service IDs")
            
            for service_id in service_ids:
                try:
                    config = {
                        'name': service_id.get('name'),
                        'description': service_id.get('description'),
                        'iam_id': service_id.get('iam_id'),
                        'account_id': service_id.get('account_id'),
                        'created_at': service_id.get('created_at'),
                        'modified_at': service_id.get('modified_at'),
                        'locked': service_id.get('locked', False)
                    }
                    
                    normalized = self.normalize(
                        resource_id=service_id.get('id', service_id.get('iam_id')),
                        resource_type='iam_service_id',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing service ID {service_id.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting service IDs")
        
        return resources
    
    def _collect_access_groups(self) -> List[Dict[str, Any]]:
        """Collect access groups."""
        resources = []
        
        try:
            self.logger.info("Collecting access groups...")
            
            response = self.client.iam_access_groups.list_access_groups(
                account_id=self.account_id
            )
            
            groups = response.get_result().get('groups', [])
            self.logger.info(f"Found {len(groups)} access groups")
            
            for group in groups:
                try:
                    # Get group members
                    members_response = self.client.iam_access_groups.list_access_group_members(
                        access_group_id=group.get('id')
                    )
                    members = members_response.get_result().get('members', [])
                    
                    config = {
                        'name': group.get('name'),
                        'description': group.get('description'),
                        'account_id': group.get('account_id'),
                        'created_at': group.get('created_at'),
                        'last_modified_at': group.get('last_modified_at'),
                        'member_count': len(members),
                        'members': [
                            {
                                'iam_id': m.get('iam_id'),
                                'type': m.get('type'),
                                'name': m.get('name')
                            } for m in members
                        ]
                    }
                    
                    normalized = self.normalize(
                        resource_id=group.get('id'),
                        resource_type='iam_access_group',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing access group {group.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting access groups")
        
        return resources
    
    def _collect_policies(self) -> List[Dict[str, Any]]:
        """Collect IAM policies."""
        resources = []
        
        try:
            self.logger.info("Collecting IAM policies...")
            
            response = self.client.iam_policy.list_policies(
                account_id=self.account_id
            )
            
            policies = response.get_result().get('policies', [])
            self.logger.info(f"Found {len(policies)} policies")
            
            for policy in policies:
                try:
                    config = {
                        'type': policy.get('type'),
                        'description': policy.get('description'),
                        'subjects': policy.get('subjects', []),
                        'roles': [role.get('role_id') for role in policy.get('roles', [])],
                        'resources': policy.get('resources', []),
                        'created_at': policy.get('created_at'),
                        'last_modified_at': policy.get('last_modified_at'),
                        'state': policy.get('state')
                    }
                    
                    normalized = self.normalize(
                        resource_id=policy.get('id'),
                        resource_type='iam_policy',
                        configuration=config
                    )
                    resources.append(normalized)
                    
                except Exception as e:
                    self.handle_error(e, f"processing policy {policy.get('id')}")
                    
        except Exception as e:
            self.handle_error(e, "collecting policies")
        
        return resources

# Made with Bob
