"""
FOCUS Billing API: Get Supported Feature

Provides an API endpoint to retrieve detailed information about a specific
FOCUS supported feature, including the full content and metadata.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from moose_lib import ConsumptionApi, EgressConfig

from app.focus_billing.supported_features_loader import FocusSupportedFeaturesLoader
from app.focus_billing.models import FocusSupportedFeature, FocusFeatureLevel
from .exceptions import handle_focus_billing_error, FeatureNotFoundError


class FocusSupportedFeatureDetail(BaseModel):
    """Detailed information about a FOCUS supported feature"""
    name: str = Field(description="Feature name identifier")
    title: str = Field(description="Feature title")
    description: str = Field(description="Feature description")
    feature_level: FocusFeatureLevel = Field(description="Feature level")
    content: str = Field(description="Full feature content from markdown")
    parsed_sections: Dict[str, Any] = Field(description="Parsed content sections")
    related_columns: List[str] = Field(description="Related FOCUS columns")


class GetSupportedFeatureResponse(BaseModel):
    """Response model for getting a FOCUS supported feature"""
    feature: Optional[FocusSupportedFeatureDetail] = Field(None, description="Feature details")
    found: bool = Field(description="Whether the feature was found")


class GetSupportedFeatureQueryParams(BaseModel):
    """Query parameters for getting a FOCUS supported feature"""
    name: str = Field(description="Feature name identifier")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Feature name cannot be empty")
        return v.strip()


def get_supported_feature(client, params: GetSupportedFeatureQueryParams) -> GetSupportedFeatureResponse:
    """
    Get detailed information about a specific FOCUS supported feature.
    
    Args:
        client: ClickHouse client (not used for this metadata operation)
        params: Query parameters with feature name
        
    Returns:
        GetSupportedFeatureResponse with feature details
        
    Raises:
        FeatureNotFoundError: If the requested feature is not found
        Exception: For other unexpected errors
    """
    try:
        # Load the specific feature
        features_loader = FocusSupportedFeaturesLoader()
        feature = features_loader.get_feature(params.name)
        
        if not feature:
            return GetSupportedFeatureResponse(
                feature=None,
                found=False
            )
        
        # Parse the content for additional structure
        parsed_sections = _parse_feature_content(feature.content)
        
        # Extract related columns
        related_columns = _extract_related_columns(feature.content, parsed_sections)
        
        # Create detailed response
        feature_detail = FocusSupportedFeatureDetail(
            name=feature.name,
            title=feature.title,
            description=feature.description,
            feature_level=feature.feature_level,
            content=feature.content,
            parsed_sections=parsed_sections,
            related_columns=related_columns
        )
        
        return GetSupportedFeatureResponse(
            feature=feature_detail,
            found=True
        )
        
    except Exception as e:
        # Log the error and re-raise for proper handling
        print(f"Error in get_supported_feature: {str(e)}")
        raise


def _parse_feature_content(content: str) -> Dict[str, Any]:
    """
    Parse feature content into structured sections.
    
    Args:
        content: Raw markdown content
        
    Returns:
        Dictionary with parsed sections
    """
    import re
    
    sections = {}
    
    # Extract description
    desc_match = re.search(r'##\s+Description\s*\n\n(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
    if desc_match:
        sections['description'] = desc_match.group(1).strip()
    
    # Extract directly dependent columns
    deps_match = re.search(r'##\s+Directly Dependent Columns\s*\n\n(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
    if deps_match:
        deps_text = deps_match.group(1).strip()
        columns = re.findall(r'^\*\s+(.+)$', deps_text, re.MULTILINE)
        sections['dependent_columns'] = [col.strip() for col in columns]
    
    # Extract supporting columns
    support_match = re.search(r'##\s+Supporting Columns\s*\n\n(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
    if support_match:
        support_text = support_match.group(1).strip()
        columns = re.findall(r'^\*\s+(.+)$', support_text, re.MULTILINE)
        sections['supporting_columns'] = [col.strip() for col in columns]
    
    # Extract example SQL
    sql_match = re.search(r'##\s+Example SQL Query\s*\n\n```sql\n(.*?)\n```', content, re.DOTALL)
    if sql_match:
        sections['example_sql'] = sql_match.group(1).strip()
    
    # Extract version information
    version_match = re.search(r'##\s+Introduced \(Version\)\s*\n\n(.+)', content)
    if version_match:
        sections['introduced_version'] = version_match.group(1).strip()
    
    # Extract any additional sections
    section_headers = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
    sections['section_headers'] = section_headers
    
    return sections


def _extract_related_columns(content: str, parsed_sections: Dict[str, Any]) -> List[str]:
    """
    Extract all related FOCUS columns from the feature content.
    
    Args:
        content: Raw markdown content
        parsed_sections: Parsed content sections
        
    Returns:
        List of related column names
    """
    columns = set()
    
    # Add columns from parsed sections
    if 'dependent_columns' in parsed_sections:
        columns.update(parsed_sections['dependent_columns'])
    
    if 'supporting_columns' in parsed_sections:
        columns.update(parsed_sections['supporting_columns'])
    
    # Extract additional columns from SQL examples
    if 'example_sql' in parsed_sections:
        sql = parsed_sections['example_sql']
        # Find column names in SELECT and WHERE clauses
        import re
        column_pattern = r'\b([A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)*)\b'
        sql_columns = re.findall(column_pattern, sql)
        
        # Filter out SQL keywords and functions
        sql_keywords = {
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'HAVING', 
            'AND', 'OR', 'NOT', 'IN', 'AS', 'SUM', 'COUNT', 'AVG', 'MAX', 'MIN'
        }
        
        for col in sql_columns:
            if col not in sql_keywords and len(col) > 2:
                columns.add(col)
    
    return sorted(list(columns))


# Create the consumption API
get_supported_feature_api = ConsumptionApi[GetSupportedFeatureQueryParams, GetSupportedFeatureResponse](
    "getSupportedFeature",
    query_function=get_supported_feature,
    source="focus_billing",  # Logical source name
    config=EgressConfig()
)