import React, { useState, useMemo } from 'react';
import { PluginMetadata } from '../types/focus-types';

interface PluginDiscoveryProps {
  availablePlugins: PluginMetadata[];
  installedPlugins: PluginMetadata[];
  onInstallPlugin: (plugin: PluginMetadata) => void;
  onRefresh: () => void;
}

export const PluginDiscovery: React.FC<PluginDiscoveryProps> = ({
  availablePlugins,
  installedPlugins,
  onInstallPlugin,
  onRefresh
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'rating' | 'downloads' | 'updated'>('name');

  const installedPluginIds = useMemo(() => 
    new Set(installedPlugins.map(p => p.id)), 
    [installedPlugins]
  );

  const categories = useMemo(() => {
    const cats = new Set(availablePlugins.map(p => p.category));
    return ['all', ...Array.from(cats)];
  }, [availablePlugins]);

  const filteredAndSortedPlugins = useMemo(() => {
    let filtered = availablePlugins.filter(plugin => {
      const matchesSearch = plugin.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           plugin.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           plugin.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      
      const matchesCategory = selectedCategory === 'all' || plugin.category === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });

    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'rating':
          return (b.rating || 0) - (a.rating || 0);
        case 'downloads':
          return (b.downloadCount || 0) - (a.downloadCount || 0);
        case 'updated':
          return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
        default:
          return a.name.localeCompare(b.name);
      }
    });
  }, [availablePlugins, searchTerm, selectedCategory, sortBy]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const renderStars = (rating?: number) => {
    if (!rating) return null;
    
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    
    for (let i = 0; i < fullStars; i++) {
      stars.push(<span key={i} className="star filled">★</span>);
    }
    
    if (hasHalfStar) {
      stars.push(<span key="half" className="star half">★</span>);
    }
    
    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<span key={`empty-${i}`} className="star empty">☆</span>);
    }
    
    return <div className="rating">{stars}</div>;
  };

  return (
    <div className="plugin-discovery">
      <div className="discovery-header">
        <div className="search-filters">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search plugins..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          
          <div className="filter-controls">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="category-filter"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="sort-filter"
            >
              <option value="name">Sort by Name</option>
              <option value="rating">Sort by Rating</option>
              <option value="downloads">Sort by Downloads</option>
              <option value="updated">Sort by Last Updated</option>
            </select>
          </div>
        </div>
        
        <div className="discovery-actions">
          <button onClick={onRefresh} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      <div className="plugins-grid">
        {filteredAndSortedPlugins.length === 0 ? (
          <div className="no-plugins">
            <p>No plugins found matching your criteria.</p>
          </div>
        ) : (
          filteredAndSortedPlugins.map(plugin => {
            const isInstalled = installedPluginIds.has(plugin.id);
            
            return (
              <div key={plugin.id} className="plugin-card">
                <div className="plugin-header">
                  {plugin.iconUrl && (
                    <img src={plugin.iconUrl} alt={plugin.name} className="plugin-icon" />
                  )}
                  <div className="plugin-title">
                    <h3>{plugin.name}</h3>
                    <span className="plugin-version">v{plugin.version}</span>
                  </div>
                  <div className="plugin-category">
                    <span className={`category-badge ${plugin.category}`}>
                      {plugin.category}
                    </span>
                  </div>
                </div>

                <div className="plugin-content">
                  <p className="plugin-description">{plugin.description}</p>
                  
                  <div className="plugin-author">
                    <span>by {plugin.author}</span>
                  </div>

                  <div className="plugin-tags">
                    {plugin.tags.map(tag => (
                      <span key={tag} className="tag">
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="plugin-stats">
                    {plugin.rating && (
                      <div className="stat">
                        {renderStars(plugin.rating)}
                        <span className="rating-value">({plugin.rating.toFixed(1)})</span>
                      </div>
                    )}
                    
                    {plugin.downloadCount && (
                      <div className="stat">
                        <span className="downloads">{plugin.downloadCount.toLocaleString()} downloads</span>
                      </div>
                    )}
                    
                    <div className="stat">
                      <span className="last-updated">Updated {formatDate(plugin.lastUpdated)}</span>
                    </div>
                  </div>
                </div>

                <div className="plugin-actions">
                  {plugin.documentationUrl && (
                    <a
                      href={plugin.documentationUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="docs-link"
                    >
                      Documentation
                    </a>
                  )}
                  
                  <button
                    onClick={() => onInstallPlugin(plugin)}
                    disabled={isInstalled}
                    className={`install-button ${isInstalled ? 'installed' : ''}`}
                  >
                    {isInstalled ? 'Installed' : 'Install'}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default PluginDiscovery;