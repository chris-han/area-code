"""
Resource Tracking Engine for Azure Billing Data

This module provides the ResourceTrackingEngine class for applying resource tracking
patterns to Azure billing data based on patterns stored in the d_application_tag table.
"""

import logging
import polars as pl
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ResourceTrackingEngine:
    """
    Engine for applying resource tracking patterns to Azure billing data
    
    Loads patterns from d_application_tag table and applies them to billing records
    with priority-based matching and audit logging for conflicts.
    """
    
    def __init__(self, clickhouse_client=None):
        """
        Initialize the resource tracking engine
        
        Args:
            clickhouse_client: ClickHouse client instance (optional for now)
        """
        self.client = clickhouse_client
        self.patterns: List[Tuple[str, str, int]] = []
        self.patterns_loaded_at: Optional[datetime] = None
        self.cache_duration_minutes = 30  # Cache patterns for 30 minutes
        
        logger.info("Initialized ResourceTrackingEngine")
    
    def _should_refresh_patterns(self) -> bool:
        """
        Check if patterns cache should be refreshed
        
        Returns:
            True if patterns should be reloaded, False otherwise
        """
        if not self.patterns_loaded_at:
            return True
        
        # Check if cache has expired
        cache_age = datetime.now() - self.patterns_loaded_at
        return cache_age.total_seconds() > (self.cache_duration_minutes * 60)
    
    def load_patterns(self) -> List[Tuple[str, str, int]]:
        """
        Load resource tracking patterns from d_application_tag table
        
        Returns:
            List of tuples containing (pattern, application_service, priority)
            Priority: 1=instance_id, 2=resource_group, 3=subscription_guid
            
        Raises:
            Exception: If database connection fails or query errors
        """
        try:
            # For now, return mock patterns since we don't have ClickHouse client setup
            # This will be replaced with actual database query in production
            if self.client is None:
                logger.warning("No ClickHouse client provided, using mock patterns")
                mock_patterns = [
                    # (pattern, application_service, priority)
                    ("*/subscriptions/12345678-1234-1234-1234-123456789012/*", "app-service-1", 3),
                    ("*/resourceGroups/rg-production/*", "app-service-2", 2),
                    ("*/virtualMachines/vm-web-01", "web-service", 1),
                    ("*/virtualMachines/vm-db-*", "database-service", 1),
                    ("*/subscriptions/87654321-4321-4321-4321-210987654321/*", "app-service-3", 3),
                ]
                self.patterns = mock_patterns
                self.patterns_loaded_at = datetime.now()
                logger.info(f"Loaded {len(mock_patterns)} mock resource tracking patterns")
                return mock_patterns
            
            # TODO: Implement actual ClickHouse query when client is available
            query = """
            SELECT 
                pattern,
                application_service,
                CASE 
                    WHEN pattern LIKE '%/virtualMachines/%' OR pattern LIKE '%instance_id%' THEN 1
                    WHEN pattern LIKE '%/resourceGroups/%' THEN 2
                    WHEN pattern LIKE '%/subscriptions/%' THEN 3
                    ELSE 4
                END as priority
            FROM d_application_tag 
            WHERE active = 1
            ORDER BY priority ASC, pattern
            """
            
            # Execute query (placeholder for actual implementation)
            # result = self.client.execute(query)
            # patterns = [(row[0], row[1], row[2]) for row in result]
            
            patterns = []  # Placeholder
            self.patterns = patterns
            self.patterns_loaded_at = datetime.now()
            
            logger.info(f"Loaded {len(patterns)} resource tracking patterns from database")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to load resource tracking patterns: {str(e)}")
            # Keep existing patterns if reload fails
            if self.patterns:
                logger.warning("Using cached patterns due to reload failure")
                return self.patterns
            raise
    
    def _match_pattern(self, instance_id: str, resource_group: str, subscription_guid: str, 
                      pattern: str, priority: int) -> Optional[Tuple[str, int, str]]:
        """
        Check if a billing record matches a specific pattern
        
        Args:
            instance_id: Instance ID from billing record
            resource_group: Resource group from billing record  
            subscription_guid: Subscription GUID from billing record
            pattern: Pattern to match against
            priority: Pattern priority (1=highest, 3=lowest)
            
        Returns:
            Tuple of (matched_field, priority, pattern) if match found, None otherwise
        """
        try:
            # Convert pattern to lowercase for case-insensitive matching
            pattern_lower = pattern.lower() if pattern else ""
            
            # Priority 1: Instance ID matching
            if priority == 1 and instance_id:
                instance_id_lower = instance_id.lower()
                if self._wildcard_match(instance_id_lower, pattern_lower):
                    return ("instance_id", priority, pattern)
            
            # Priority 2: Resource Group matching
            if priority == 2 and resource_group:
                resource_group_lower = resource_group.lower()
                # Check if pattern matches resource group path
                if self._wildcard_match(resource_group_lower, pattern_lower) or \
                   f"/resourcegroups/{resource_group_lower}" in pattern_lower:
                    return ("resource_group", priority, pattern)
            
            # Priority 3: Subscription GUID matching
            if priority == 3 and subscription_guid:
                subscription_guid_lower = subscription_guid.lower()
                # Check if pattern matches subscription
                if self._wildcard_match(subscription_guid_lower, pattern_lower) or \
                   f"/subscriptions/{subscription_guid_lower}" in pattern_lower:
                    return ("subscription_guid", priority, pattern)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error matching pattern '{pattern}': {str(e)}")
            return None
    
    def _wildcard_match(self, text: str, pattern: str) -> bool:
        """
        Simple wildcard matching with * support
        
        Args:
            text: Text to match against
            pattern: Pattern with * wildcards
            
        Returns:
            True if text matches pattern, False otherwise
        """
        if not pattern or not text:
            return False
        
        # Handle simple cases
        if pattern == "*":
            return True
        if "*" not in pattern:
            return text == pattern
        
        # Split pattern by * and check each part
        parts = pattern.split("*")
        
        # Check if text starts with first part (if not empty)
        if parts[0] and not text.startswith(parts[0]):
            return False
        
        # Check if text ends with last part (if not empty)
        if parts[-1] and not text.endswith(parts[-1]):
            return False
        
        # Check middle parts exist in order
        current_pos = len(parts[0]) if parts[0] else 0
        for part in parts[1:-1]:
            if part:
                pos = text.find(part, current_pos)
                if pos == -1:
                    return False
                current_pos = pos + len(part)
        
        return True
    
    def apply_tracking(self, df: pl.DataFrame) -> Tuple[pl.Series, pl.DataFrame]:
        """
        Apply vectorized resource tracking with audit logging
        
        Args:
            df: Polars DataFrame with billing records containing:
                - instance_id (required)
                - resource_group (optional)
                - subscription_guid (optional)
                
        Returns:
            Tuple containing:
            - Series with resource tracking assignments
            - DataFrame with audit log entries for conflicts/multiple matches
            
        Raises:
            ValueError: If required columns are missing
        """
        try:
            # Validate required columns
            required_cols = ['instance_id']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Ensure we have current patterns
            patterns = self.get_patterns()
            if not patterns:
                logger.warning("No resource tracking patterns available")
                # Return empty tracking and audit log
                empty_tracking = pl.Series("resource_tracking", [None] * len(df))
                empty_audit = pl.DataFrame({
                    'instance_id': [],
                    'matched_patterns': [],
                    'conflict_type': [],
                    'timestamp': []
                }, schema={
                    'instance_id': pl.Utf8,
                    'matched_patterns': pl.Utf8,
                    'conflict_type': pl.Utf8,
                    'timestamp': pl.Datetime
                })
                return empty_tracking, empty_audit
            
            logger.info(f"Applying resource tracking to {len(df)} records using {len(patterns)} patterns")
            
            # Initialize tracking results
            tracking_results = []
            audit_entries = []
            
            # Process each record
            for i in range(len(df)):
                row = df.row(i, named=True)
                instance_id = row.get('instance_id', '')
                resource_group = row.get('resource_group', '')
                subscription_guid = row.get('subscription_guid', '')
                
                # Find all matching patterns for this record
                matches = []
                for pattern, app_service, priority in patterns:
                    match_result = self._match_pattern(
                        instance_id, resource_group, subscription_guid, 
                        pattern, priority
                    )
                    if match_result:
                        matches.append((app_service, match_result[1], pattern, match_result[0]))
                
                # Process matches based on priority
                if not matches:
                    # No matches found
                    tracking_results.append(None)
                elif len(matches) == 1:
                    # Single match - use it
                    tracking_results.append(matches[0][0])  # app_service
                else:
                    # Multiple matches - apply priority rules and log conflict
                    matches.sort(key=lambda x: x[1])  # Sort by priority (1=highest)
                    
                    # Check for conflicts at same priority level
                    highest_priority = matches[0][1]
                    same_priority_matches = [m for m in matches if m[1] == highest_priority]
                    
                    if len(same_priority_matches) > 1:
                        # Conflict at same priority level
                        conflict_patterns = [f"{m[2]}→{m[0]}" for m in same_priority_matches]
                        audit_entries.append({
                            'instance_id': instance_id,
                            'matched_patterns': "; ".join(conflict_patterns),
                            'conflict_type': f'multiple_priority_{highest_priority}',
                            'timestamp': datetime.now()
                        })
                        logger.warning(f"Priority conflict for {instance_id}: {conflict_patterns}")
                        
                        # Use first match alphabetically for consistency
                        same_priority_matches.sort(key=lambda x: x[0])  # Sort by app_service name
                        tracking_results.append(same_priority_matches[0][0])
                    else:
                        # Clear winner by priority
                        tracking_results.append(matches[0][0])
                        
                        # Log multiple matches for audit (not necessarily a conflict)
                        if len(matches) > 1:
                            all_patterns = [f"{m[2]}→{m[0]}(p{m[1]})" for m in matches]
                            audit_entries.append({
                                'instance_id': instance_id,
                                'matched_patterns': "; ".join(all_patterns),
                                'conflict_type': 'multiple_priority_resolved',
                                'timestamp': datetime.now()
                            })
            
            # Create result series
            tracking_series = pl.Series("resource_tracking", tracking_results)
            
            # Create audit DataFrame
            if audit_entries:
                audit_df = pl.DataFrame(audit_entries)
            else:
                # Empty audit log
                audit_df = pl.DataFrame({
                    'instance_id': [],
                    'matched_patterns': [],
                    'conflict_type': [],
                    'timestamp': []
                }, schema={
                    'instance_id': pl.Utf8,
                    'matched_patterns': pl.Utf8,
                    'conflict_type': pl.Utf8,
                    'timestamp': pl.Datetime
                })
            
            # Log summary statistics
            total_records = len(df)
            matched_records = sum(1 for x in tracking_results if x is not None)
            conflict_records = len(audit_entries)
            
            logger.info(f"Resource tracking complete: {matched_records}/{total_records} matched, "
                       f"{conflict_records} conflicts/multiple matches")
            
            return tracking_series, audit_df
            
        except Exception as e:
            logger.error(f"Failed to apply resource tracking: {str(e)}")
            raise
    
    def generate_audit_summary(self, audit_df: pl.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics from audit log
        
        Args:
            audit_df: Audit log DataFrame from apply_tracking
            
        Returns:
            Dictionary with audit summary statistics
        """
        try:
            if len(audit_df) == 0:
                return {
                    'total_conflicts': 0,
                    'conflict_types': {},
                    'top_conflicted_instances': []
                }
            
            # Count conflicts by type
            conflict_counts = audit_df.group_by('conflict_type').agg(
                pl.count().alias('count')
            ).to_dicts()
            
            conflict_types = {row['conflict_type']: row['count'] for row in conflict_counts}
            
            # Find most frequently conflicted instances
            instance_counts = audit_df.group_by('instance_id').agg(
                pl.count().alias('count')
            ).sort('count', descending=True).limit(10).to_dicts()
            
            top_instances = [(row['instance_id'], row['count']) for row in instance_counts]
            
            summary = {
                'total_conflicts': len(audit_df),
                'conflict_types': conflict_types,
                'top_conflicted_instances': top_instances
            }
            
            logger.info(f"Audit summary: {summary['total_conflicts']} total conflicts")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate audit summary: {str(e)}")
            return {'error': str(e)}

    def get_patterns(self, force_refresh: bool = False) -> List[Tuple[str, str, int]]:
        """
        Get current resource tracking patterns, loading if necessary
        
        Args:
            force_refresh: Force reload patterns from database
            
        Returns:
            List of current patterns
        """
        if force_refresh or self._should_refresh_patterns():
            return self.load_patterns()
        return self.patterns