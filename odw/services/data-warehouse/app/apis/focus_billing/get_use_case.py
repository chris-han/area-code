"""
FOCUS Billing API: Get Use Case

Provides an API endpoint to retrieve detailed information about a specific
FOCUS use case query, including the SQL and parameter specifications.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from moose_lib import ConsumptionApi, EgressConfig

from app.focus_billing.query_loader import FocusQueryLoader, FocusQueryParameterExtractor
from app.focus_billing.models import FocusQuery
from .exceptions import handle_focus_billing_error, QueryNotFoundError


class FocusUseCaseDetail(BaseModel):
    """Detailed information about a FOCUS use case query"""
    slug: str = Field(description="Unique query identifier")
    name: str = Field(description="Human-readable query name")
    description: Optional[str] = Field(None, description="Query description")
    category: Optional[str] = Field(None, description="Query category")
    tags: List[str] = Field(default_factory=list, description="Query tags")
    sql: str = Field(description="SQL query text")
    parameters: List[str] = Field(default_factory=list, description="Required parameters")
    parameter_types: Dict[str, str] = Field(default_factory=dict, description="Suggested parameter types")
    parameter_analysis: Dict[str, Any] = Field(default_factory=dict, description="Parameter analysis")


class GetFocusUseCaseResponse(BaseModel):
    """Response model for getting a FOCUS use case"""
    use_case: Optional[FocusUseCaseDetail] = Field(None, description="Use case details")
    found: bool = Field(description="Whether the use case was found")


class GetFocusUseCaseQueryParams(BaseModel):
    """Query parameters for getting a FOCUS use case"""
    slug: str = Field(description="Use case slug identifier")
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v or not v.strip():
            raise ValueError("Slug cannot be empty")
        return v.strip()


def get_focus_use_case(client, params: GetFocusUseCaseQueryParams) -> GetFocusUseCaseResponse:
    """
    Get detailed information about a specific FOCUS use case query.
    
    Args:
        client: ClickHouse client (not used for this metadata operation)
        params: Query parameters with slug
        
    Returns:
        GetFocusUseCaseResponse with use case details
        
    Raises:
        QueryNotFoundError: If the requested query is not found
        Exception: For other unexpected errors
    """
    try:
        # Load the specific query
        query_loader = FocusQueryLoader()
        query = query_loader.get_query(params.slug)
        
        if not query:
            return GetFocusUseCaseResponse(
                use_case=None,
                found=False
            )
        
        # Analyze parameters
        parameter_extractor = FocusQueryParameterExtractor()
        parameter_types = parameter_extractor.suggest_parameter_types(query.parameters)
        parameter_analysis = parameter_extractor.analyze_query_parameters(query.sql)
        
        # Create detailed response
        use_case_detail = FocusUseCaseDetail(
            slug=query.slug,
            name=query.name,
            description=query.description,
            category=query.category,
            tags=query.tags,
            sql=query.sql,
            parameters=query.parameters,
            parameter_types=parameter_types,
            parameter_analysis=parameter_analysis
        )
        
        return GetFocusUseCaseResponse(
            use_case=use_case_detail,
            found=True
        )
        
    except Exception as e:
        # Log the error and re-raise for proper handling
        print(f"Error in get_focus_use_case: {str(e)}")
        raise


# Create the consumption API
get_focus_use_case_api = ConsumptionApi[GetFocusUseCaseQueryParams, GetFocusUseCaseResponse](
    "getFocusUseCase",
    query_function=get_focus_use_case,
    source="focus_billing",  # Logical source name
    config=EgressConfig()
)