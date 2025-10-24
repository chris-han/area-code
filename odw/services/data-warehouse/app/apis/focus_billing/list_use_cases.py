"""
FOCUS Billing API: List Use Cases

Provides an API endpoint to list all available FOCUS use case queries
with their metadata for discovery and selection.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from moose_lib import ConsumptionApi, EgressConfig

from app.focus_billing.query_loader import FocusQueryLoader
from app.focus_billing.models import FocusQuery
from .exceptions import handle_focus_billing_error, ConfigurationError


class FocusUseCaseMetadata(BaseModel):
    """Metadata for a FOCUS use case query"""
    slug: str = Field(description="Unique query identifier")
    name: str = Field(description="Human-readable query name")
    description: Optional[str] = Field(None, description="Query description")
    category: Optional[str] = Field(None, description="Query category")
    tags: List[str] = Field(default_factory=list, description="Query tags")
    parameters: List[str] = Field(default_factory=list, description="Required parameters")
    parameter_count: int = Field(description="Number of parameters required")


class ListFocusUseCasesResponse(BaseModel):
    """Response model for listing FOCUS use cases"""
    use_cases: List[FocusUseCaseMetadata] = Field(description="List of available use cases")
    total_count: int = Field(description="Total number of use cases")
    categories: List[str] = Field(description="Available categories")


class ListFocusUseCasesQueryParams(BaseModel):
    """Query parameters for filtering FOCUS use cases"""
    category: Optional[str] = Field(None, description="Filter by category")
    tag: Optional[str] = Field(None, description="Filter by tag")
    search: Optional[str] = Field(None, description="Search in name and description")


def list_focus_use_cases(client, params: ListFocusUseCasesQueryParams) -> ListFocusUseCasesResponse:
    """
    List all available FOCUS use case queries with metadata.
    
    Args:
        client: ClickHouse client (not used for this metadata operation)
        params: Query parameters for filtering
        
    Returns:
        ListFocusUseCasesResponse with use case metadata
        
    Raises:
        ConfigurationError: If FOCUS configuration is invalid
        Exception: For other unexpected errors
    """
    try:
        # Load queries using the query loader
        query_loader = FocusQueryLoader()
        queries = query_loader.load_queries()
        
        if not queries:
            raise ConfigurationError("No FOCUS use case queries found. Check FOCUS specification path configuration.")
        
        # Convert to metadata objects
        use_cases = []
        categories = set()
        
        for slug, query in queries.items():
            # Apply filters
            if params.category and query.category != params.category:
                continue
                
            if params.tag and params.tag not in query.tags:
                continue
                
            if params.search:
                search_text = params.search.lower()
                if (search_text not in query.name.lower() and 
                    search_text not in (query.description or "").lower()):
                    continue
            
            # Create metadata object
            metadata = FocusUseCaseMetadata(
                slug=query.slug,
                name=query.name,
                description=query.description,
                category=query.category,
                tags=query.tags,
                parameters=query.parameters,
                parameter_count=len(query.parameters)
            )
            
            use_cases.append(metadata)
            
            if query.category:
                categories.add(query.category)
        
        # Sort by name for consistent ordering
        use_cases.sort(key=lambda x: x.name)
        
        return ListFocusUseCasesResponse(
            use_cases=use_cases,
            total_count=len(use_cases),
            categories=sorted(list(categories))
        )
        
    except Exception as e:
        # Log the error and re-raise for proper handling
        print(f"Error in list_focus_use_cases: {str(e)}")
        raise


# Create the consumption API
list_focus_use_cases_api = ConsumptionApi[ListFocusUseCasesQueryParams, ListFocusUseCasesResponse](
    "listFocusUseCases",
    query_function=list_focus_use_cases,
    source="focus_billing",  # Logical source name
    config=EgressConfig()
)