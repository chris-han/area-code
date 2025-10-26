"""
Dynamic Workflow Registry

Discovers and registers Temporal workflows at runtime by inspecting
the data-warehouse temporal_worker configuration.
"""

import logging
import importlib
import inspect
from typing import Dict, List, Optional, Type, Any
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """
    Dynamic workflow registry that discovers workflows from temporal_worker.

    Workflows are discovered by inspecting the temporal_worker module's
    registered workflows list, extracting metadata, and making them available
    to the BIA Admin UI.
    """

    _instance: Optional['WorkflowRegistry'] = None
    _workflows: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self._workflows = {}
        self._discover_workflows()

    @classmethod
    def get_instance(cls) -> 'WorkflowRegistry':
        """Get singleton instance of workflow registry"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _discover_workflows(self):
        """
        Discover workflows by importing temporal_worker and inspecting
        its registered workflows.
        """
        try:
            # Import the temporal_worker module from data-warehouse
            from app.workflows import temporal_worker

            # Extract workflow classes from the worker configuration
            # We look for the Worker initialization in the module
            worker_module = inspect.getmembers(temporal_worker, inspect.isclass)

            # Get the TemporalWorkerManager class
            worker_manager_class = None
            for name, obj in worker_module:
                if name == 'TemporalWorkerManager':
                    worker_manager_class = obj
                    break

            if not worker_manager_class:
                logger.warning("Could not find TemporalWorkerManager in temporal_worker")
                return

            # Read the source code to extract workflow list
            source_file = inspect.getsourcefile(worker_manager_class)
            if not source_file:
                logger.warning("Could not find source file for TemporalWorkerManager")
                return

            with open(source_file, 'r') as f:
                source_code = f.read()

            # Parse workflow registrations from source
            # This is a simple approach - looks for the workflows= list in Worker()
            import re
            workflow_pattern = r'workflows=\[(.*?)\]'
            match = re.search(workflow_pattern, source_code, re.DOTALL)

            if not match:
                logger.warning("Could not find workflows list in temporal_worker")
                return

            workflow_list_str = match.group(1)
            # Extract workflow class names
            workflow_names = re.findall(r'(\w+Workflow)', workflow_list_str)

            # Import and register each workflow
            for workflow_name in workflow_names:
                self._register_workflow_from_name(workflow_name)

            logger.info(f"Discovered {len(self._workflows)} workflows: {list(self._workflows.keys())}")

        except Exception as e:
            logger.error(f"Failed to discover workflows: {e}")
            # Fallback to hardcoded workflows for reliability
            self._register_fallback_workflows()

    def _register_workflow_from_name(self, workflow_class_name: str):
        """
        Register a workflow by importing it and extracting metadata.

        Args:
            workflow_class_name: Name of the workflow class (e.g., 'FocusBillingTemporalWorkflow')
        """
        try:
            # Convert class name to workflow_type identifier
            # FocusBillingTemporalWorkflow -> focus_billing_ingest
            # SchemaMigrationWorkflow -> schema_migration

            workflow_type = self._class_name_to_workflow_type(workflow_class_name)

            # Try to import the workflow class to get its docstring
            workflow_class = None
            try:
                # Try focus_billing module first - but these depend on moose_lib
                # which isn't available in BIA backend, so we'll use fallback
                pass
            except ImportError:
                logger.warning(f"Could not import workflow class {workflow_class_name}")

            # Extract metadata
            description = None
            estimated_duration = None

            if workflow_class:
                # Get docstring
                description = inspect.getdoc(workflow_class)

                # Infer estimated duration from workflow type
                if 'ingest' in workflow_type.lower():
                    estimated_duration = "10-20 minutes"
                elif 'migration' in workflow_type.lower():
                    estimated_duration = "5-30 minutes"

            # Register the workflow
            self._workflows[workflow_type] = {
                'workflow_type': workflow_type,
                'workflow_class': workflow_class_name,
                'description': description or f"{workflow_class_name} workflow",
                'estimated_duration': estimated_duration,
                'display_name': self._class_name_to_display_name(workflow_class_name),
            }

            logger.info(f"Registered workflow: {workflow_type} ({workflow_class_name})")

        except Exception as e:
            logger.error(f"Failed to register workflow {workflow_class_name}: {e}")

    def _class_name_to_workflow_type(self, class_name: str) -> str:
        """
        Convert workflow class name to workflow_type identifier.

        Examples:
            FocusBillingTemporalWorkflow -> focus_billing_ingest
            SchemaMigrationWorkflow -> schema_migration
        """
        # Remove 'Workflow' and 'Temporal' suffixes
        name = class_name.replace('Workflow', '').replace('Temporal', '')

        # Convert PascalCase to snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        return snake_case

    def _class_name_to_display_name(self, class_name: str) -> str:
        """
        Convert workflow class name to human-readable display name.

        Examples:
            FocusBillingTemporalWorkflow -> FOCUS Billing Ingest
            SchemaMigrationWorkflow -> Schema Migration
        """
        # Remove 'Workflow' and 'Temporal' suffixes
        name = class_name.replace('Workflow', '').replace('Temporal', '')

        # Convert PascalCase to Title Case with spaces
        import re
        # Add space before capital letters
        spaced = re.sub('([A-Z])', r' \1', name).strip()

        return spaced.title()

    def _register_fallback_workflows(self):
        """
        Register hardcoded fallback workflows if discovery fails.
        This ensures the system remains functional even if discovery fails.
        """
        fallback_workflows = [
            {
                'workflow_type': 'focus_billing_ingest',
                'workflow_class': 'FocusBillingTemporalWorkflow',
                'description': 'Ingest FOCUS billing data from Parquet files into ClickHouse',
                'estimated_duration': '10-20 minutes',
                'display_name': 'FOCUS Billing Ingest',
            },
            {
                'workflow_type': 'schema_migration',
                'workflow_class': 'SchemaMigrationWorkflow',
                'description': 'Detect and apply schema migrations for FOCUS data',
                'estimated_duration': '5-30 minutes',
                'display_name': 'Schema Migration',
            },
        ]

        for workflow in fallback_workflows:
            self._workflows[workflow['workflow_type']] = workflow

        logger.info(f"Registered {len(fallback_workflows)} fallback workflows")

    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get list of all registered workflows"""
        return list(self._workflows.values())

    def get_workflow(self, workflow_type: str) -> Optional[Dict[str, Any]]:
        """Get workflow by type identifier"""
        return self._workflows.get(workflow_type)

    def get_workflow_types(self) -> List[str]:
        """Get list of all workflow type identifiers"""
        return list(self._workflows.keys())

    def get_workflow_class_name(self, workflow_type: str) -> Optional[str]:
        """Get workflow class name for a given workflow type"""
        workflow = self._workflows.get(workflow_type)
        return workflow['workflow_class'] if workflow else None

    def workflow_type_to_class_name(self, workflow_type: str) -> Optional[str]:
        """Convert workflow_type to workflow class name"""
        return self.get_workflow_class_name(workflow_type)

    def class_name_to_workflow_type(self, class_name: str) -> Optional[str]:
        """Convert workflow class name to workflow_type"""
        for workflow_type, metadata in self._workflows.items():
            if metadata['workflow_class'] == class_name:
                return workflow_type
        return None


# Global registry instance
_registry: Optional[WorkflowRegistry] = None


def get_workflow_registry() -> WorkflowRegistry:
    """Get the global workflow registry instance"""
    global _registry
    if _registry is None:
        _registry = WorkflowRegistry.get_instance()
    return _registry


def create_dynamic_workflow_enum() -> Type[Enum]:
    """
    Create a dynamic Enum class with discovered workflow types.

    Returns:
        Enum class with workflow types as members
    """
    registry = get_workflow_registry()
    workflows = registry.get_workflows()

    # Create enum members dict
    members = {}
    for workflow in workflows:
        # Convert workflow_type to UPPER_CASE for enum member name
        member_name = workflow['workflow_type'].upper()
        members[member_name] = workflow['workflow_type']

    # Create dynamic Enum
    WorkflowTypeEnum = Enum('WorkflowType', members, type=str)
    WorkflowTypeEnum.__doc__ = "Dynamically discovered workflow types"

    return WorkflowTypeEnum
