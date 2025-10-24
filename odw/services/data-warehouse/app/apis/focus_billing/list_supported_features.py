"""
FOCUS Billing API: List Supported Features

Provides an API endpoint to list all FOCUS supported features
with their metadata for discovery and understanding of capabilities.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from moose_lib import ConsumptionApi, EgressConfig

from app.focus_billing.supported_features_loader import FocusSupportedFeaturesLoader, FocusSupportedFeaturesAnalyzer
from app.focus_billing.models import FocusSupportedFeature, FocusFeatureLevel
from .exceptions import handle_focus_billing_error, ConfigurationError


class FocusSupportedFeatureMetadata(BaseModel):
    """Metadata for a FOCUS supported feature"""
    name: str = Field(description="Feature name identifier")
    title: str = Field(description="Feature title")
    description: str = Field(description="Feature description")
    feature_level: FocusFeatureLevel = Field(description="Feature level (Mandatory, Recommended, Conditional)")
    has_sql_example: bool = Field(description="Whether the feature includes an SQL example")
    content_length: int = Field(description="Length of feature content in characters")


class ListSupportedFeaturesResponse(BaseModel):
    """Response model for listing FOCUS supported features"""
    features: List[FocusSupportedFeatureMetadata] = Field(description="List of supported features")
    total_count: int = Field(description="Total number of features")
    feature_levels: List[str] = Field(description="Available feature levels")
    analysis: Dict[str, Any] = Field(description="Feature analysis summary")


class ListSupportedFeaturesQueryParams(BaseModel):
    """Query parameters for filtering FOCUS supported features"""
    feature_level: Optional[FocusFeatureLevel] = Field(None, description="Filter by feature level")
    has_sql_example: Optional[bool] = Field(None, description="Filter by presence of SQL examples")
    search: Optional[str] = Field(None, description="Search in title and description")


def list_supported_features(client, params: ListSupportedFeaturesQueryParams) -> ListSupportedFeaturesResponse:
    """
    List all FOCUS supported features with metadata.
    
    Args:
        client: ClickHouse client (not used for this metadata operation)
        params: Query parameters for filtering
        
    Returns:
        ListSupportedFeaturesResponse with feature metadata
        
    Raises:
        ConfigurationError: If FOCUS configuration is invalid
        Exception: For other unexpected errors
    """
    try:
        # Load features using the features loader
        features_loader = FocusSupportedFeaturesLoader()
        features = features_loader.load_supported_features()
        
        if not features:
            raise ConfigurationError("No FOCUS supported features found. Check FOCUS specification path configuration.")
        
        # Convert to metadata objects
        feature_metadata = []
        feature_levels = set()
        
        for name, feature in features.items():
            # Check if feature has SQL example
            has_sql_example = 'example sql' in feature.content.lower() or '```sql' in feature.content.lower()
            
            # Apply filters
            if params.feature_level and feature.feature_level != params.feature_level:
                continue
                
            if params.has_sql_example is not None and has_sql_example != params.has_sql_example:
                continue
                
            if params.search:
                search_text = params.search.lower()
                if (search_text not in feature.title.lower() and 
                    search_text not in feature.description.lower()):
                    continue
            
            # Create metadata object
            metadata = FocusSupportedFeatureMetadata(
                name=feature.name,
                title=feature.title,
                description=feature.description,
                feature_level=feature.feature_level,
                has_sql_example=has_sql_example,
                content_length=len(feature.content)
            )
            
            feature_metadata.append(metadata)
            feature_levels.add(feature.feature_level.value)
        
        # Sort by title for consistent ordering
        feature_metadata.sort(key=lambda x: x.title)
        
        # Generate analysis
        analyzer = FocusSupportedFeaturesAnalyzer()
        analysis = analyzer.analyze_feature_dependencies(features)
        
        return ListSupportedFeaturesResponse(
            features=feature_metadata,
            total_count=len(feature_metadata),
            feature_levels=sorted(list(feature_levels)),
            analysis=analysis
        )
        
    except Exception as e:
        # Log the error and re-raise for proper handling
        print(f"Error in list_supported_features: {str(e)}")
        raise


# Create the consumption API
list_supported_features_api = ConsumptionApi[ListSupportedFeaturesQueryParams, ListSupportedFeaturesResponse](
    "listSupportedFeatures",
    query_function=list_supported_features,
    source="focus_billing",  # Logical source name
    config=EgressConfig()
)