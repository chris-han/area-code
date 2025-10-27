"""
FOCUS Supported Features Loader

Loads and parses FOCUS supported features from markdown files in the
specification directory, converting them into structured metadata
for API consumption.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import FocusSupportedFeature, FocusFeatureLevel
from .config import FocusBillingConfig


class FocusSupportedFeaturesLoader:
    """
    Loads and parses FOCUS supported features from markdown files.
    
    Handles:
    - Loading feature markdown files
    - Extracting structured metadata
    - Parsing feature content and dependencies
    """
    
    def __init__(self, config: Optional[FocusBillingConfig] = None):
        self.config = config or FocusBillingConfig()
        self._features_cache: Optional[Dict[str, FocusSupportedFeature]] = None
        
    def load_supported_features(self, force_reload: bool = False) -> Dict[str, FocusSupportedFeature]:
        """
        Load all FOCUS supported features from markdown files.
        
        Args:
            force_reload: If True, reload features even if cached
            
        Returns:
            Dictionary mapping feature names to FocusSupportedFeature objects
        """
        if self._features_cache is not None and not force_reload:
            return self._features_cache
            
        features_dir = Path(self.config.focus_spec_root) / "specification" / "supported_features"
        
        if not features_dir.exists():
            raise FileNotFoundError(f"Supported features directory not found: {features_dir}")
            
        features = {}
        
        # Process all markdown files in the directory
        for md_file in features_dir.glob("*.md"):
            # Skip overview and template files
            if md_file.name in ["supported_features_overview.md", "supported_features.mdpp"]:
                continue
                
            try:
                feature = self._parse_feature_file(md_file)
                if feature:
                    features[feature.name] = feature
            except Exception as e:
                print(f"Warning: Failed to parse feature file '{md_file.name}': {e}")
                continue
                
        self._features_cache = features
        return features
        
    def get_feature(self, name: str) -> Optional[FocusSupportedFeature]:
        """
        Get a specific supported feature by name.
        
        Args:
            name: Feature name identifier
            
        Returns:
            FocusSupportedFeature object or None if not found
        """
        features = self.load_supported_features()
        return features.get(name)
        
    def list_feature_names(self) -> List[str]:
        """
        Get list of all available feature names.
        
        Returns:
            List of feature name strings
        """
        features = self.load_supported_features()
        return list(features.keys())
        
    def get_features_by_level(self, level: FocusFeatureLevel) -> List[FocusSupportedFeature]:
        """
        Get features filtered by feature level.
        
        Args:
            level: Feature level to filter by
            
        Returns:
            List of FocusSupportedFeature objects
        """
        features = self.load_supported_features()
        return [f for f in features.values() if f.feature_level == level]
        
    def _parse_feature_file(self, file_path: Path) -> Optional[FocusSupportedFeature]:
        """
        Parse a single feature markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            FocusSupportedFeature object or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {file_path}: {e}")
            
        # Extract the feature name from filename
        feature_name = file_path.stem
        
        # Parse the markdown content
        parsed_content = self._parse_markdown_content(content)
        
        # Extract title (first heading)
        title = parsed_content.get('title', feature_name.replace('_', ' ').title())
        
        # Extract description
        description = parsed_content.get('description', '')
        
        # Determine feature level (default to Recommended if not specified)
        feature_level = self._determine_feature_level(content, parsed_content)
        
        return FocusSupportedFeature(
            name=feature_name,
            title=title,
            description=description,
            feature_level=feature_level,
            content=content
        )
        
    def _parse_markdown_content(self, content: str) -> Dict[str, Any]:
        """
        Parse markdown content to extract structured information.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Dictionary with parsed content sections
        """
        parsed = {}
        
        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            parsed['title'] = title_match.group(1).strip()
            
        # Extract description (content under ## Description)
        desc_match = re.search(r'##\s+Description\s*\n\n(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        if desc_match:
            parsed['description'] = desc_match.group(1).strip()
            
        # Extract dependent columns
        deps_match = re.search(r'##\s+Directly Dependent Columns\s*\n\n(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        if deps_match:
            deps_text = deps_match.group(1).strip()
            # Extract column names from bullet points
            columns = re.findall(r'^\*\s+(.+)$', deps_text, re.MULTILINE)
            parsed['dependent_columns'] = [col.strip() for col in columns]
            
        # Extract supporting columns
        support_match = re.search(r'##\s+Supporting Columns\s*\n\n(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        if support_match:
            support_text = support_match.group(1).strip()
            columns = re.findall(r'^\*\s+(.+)$', support_text, re.MULTILINE)
            parsed['supporting_columns'] = [col.strip() for col in columns]
            
        # Extract example SQL
        sql_match = re.search(r'##\s+Example SQL Query\s*\n\n```sql\n(.*?)\n```', content, re.DOTALL)
        if sql_match:
            parsed['example_sql'] = sql_match.group(1).strip()
            
        # Extract version information
        version_match = re.search(r'##\s+Introduced \(Version\)\s*\n\n(.+)', content)
        if version_match:
            parsed['introduced_version'] = version_match.group(1).strip()
            
        return parsed
        
    def _determine_feature_level(self, content: str, parsed_content: Dict[str, Any]) -> FocusFeatureLevel:
        """
        Determine the feature level based on content analysis.
        
        Args:
            content: Raw markdown content
            parsed_content: Parsed content dictionary
            
        Returns:
            FocusFeatureLevel enum value
        """
        # Look for explicit feature level indicators in the content
        content_lower = content.lower()
        
        if 'mandatory' in content_lower:
            return FocusFeatureLevel.MANDATORY
        elif 'conditional' in content_lower:
            return FocusFeatureLevel.CONDITIONAL
        else:
            # Default to Recommended for most features
            return FocusFeatureLevel.RECOMMENDED


class FocusSupportedFeaturesAnalyzer:
    """
    Utility class for analyzing supported features metadata.
    """
    
    @staticmethod
    def analyze_feature_dependencies(features: Dict[str, FocusSupportedFeature]) -> Dict[str, Any]:
        """
        Analyze dependencies between features.
        
        Args:
            features: Dictionary of loaded features
            
        Returns:
            Dictionary with dependency analysis
        """
        analysis = {
            'total_features': len(features),
            'by_level': {},
            'with_sql_examples': 0,
            'column_usage': {}
        }
        
        # Count by feature level
        for level in FocusFeatureLevel:
            analysis['by_level'][level.value] = len([
                f for f in features.values() if f.feature_level == level
            ])
            
        # Count features with SQL examples
        analysis['with_sql_examples'] = len([
            f for f in features.values() if 'example sql' in f.content.lower()
        ])
        
        # Analyze column usage across features
        column_mentions = {}
        for feature in features.values():
            # Extract column names from content (simple heuristic)
            column_pattern = r'\b([A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)*)\b'
            columns = re.findall(column_pattern, feature.content)
            
            for column in columns:
                if column not in column_mentions:
                    column_mentions[column] = []
                column_mentions[column].append(feature.name)
                
        # Keep only columns mentioned in multiple features
        analysis['column_usage'] = {
            col: features for col, features in column_mentions.items()
            if len(features) > 1
        }
        
        return analysis