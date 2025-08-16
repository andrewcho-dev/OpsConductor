/**
 * Discovery Templates Tab Component
 * Manages discovery templates for reusable configurations
 */

import React, { useState, useEffect } from 'react';
import discoveryService from '../../services/discoveryService';

const DiscoveryTemplatesTab = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const templatesData = await discoveryService.getDiscoveryTemplates(false); // Include inactive
      setTemplates(templatesData);
    } catch (err) {
      console.error('Error loading templates:', err);
      setError('Failed to load discovery templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setShowCreateModal(true);
  };

  const handleTemplateCreated = () => {
    setShowCreateModal(false);
    loadTemplates(); // Refresh list
  };

  if (loading) {
    return (
      <div className="templates-tab">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading discovery templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="templates-tab">
      {/* Header */}
      <div className="tab-header">
        <div className="header-content">
          <h2>Discovery Templates</h2>
          <p>Create and manage reusable discovery configurations</p>
        </div>
        <div className="header-actions">
          <button onClick={handleCreateTemplate} className="btn btn-primary">
            ➕ Create Template
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Templates List */}
      <div className="templates-list">
        {templates.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h3>No Templates Found</h3>
            <p>Create your first discovery template to save time on recurring scans.</p>
            <button onClick={handleCreateTemplate} className="btn btn-primary">
              Create First Template
            </button>
          </div>
        ) : (
          <div className="templates-grid">
            {templates.map(template => (
              <TemplateCard
                key={template.id}
                template={template}
                onUpdate={loadTemplates}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Template Modal */}
      {showCreateModal && (
        <CreateTemplateModal
          onClose={() => setShowCreateModal(false)}
          onTemplateCreated={handleTemplateCreated}
        />
      )}
    </div>
  );
};

// Template Card Component
const TemplateCard = ({ template, onUpdate }) => {
  const [showDetails, setShowDetails] = useState(false);

  const handleUseTemplate = () => {
    // This would typically trigger the new job modal with this template pre-selected
    console.log('Use template:', template.id);
  };

  return (
    <div className="template-card">
      <div className="template-header">
        <div className="template-info">
          <h3>{template.name}</h3>
          {template.description && (
            <p className="template-description">{template.description}</p>
          )}
        </div>
        <div className="template-status">
          <span className={`status-badge ${template.is_active ? 'active' : 'inactive'}`}>
            {template.is_active ? '✅ active' : '⏸️ inactive'}
          </span>
        </div>
      </div>

      <div className="template-summary">
        <div className="summary-item">
          <span className="summary-label">Networks:</span>
          <span className="summary-value">
            {template.network_ranges.slice(0, 2).join(', ')}
            {template.network_ranges.length > 2 && ` +${template.network_ranges.length - 2} more`}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Ports:</span>
          <span className="summary-value">
            {template.common_ports.length > 0 
              ? `${template.common_ports.slice(0, 5).join(', ')}${template.common_ports.length > 5 ? '...' : ''}`
              : 'Default ports'
            }
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Created:</span>
          <span className="summary-value">
            {discoveryService.formatDiscoveryTime(template.created_at)}
          </span>
        </div>
      </div>

      <div className="template-features">
        <div className="feature-list">
          {template.enable_service_detection && (
            <span className="feature-badge">🔍 Service Detection</span>
          )}
          {template.enable_hostname_resolution && (
            <span className="feature-badge">🌐 Hostname Resolution</span>
          )}
          {template.enable_snmp && (
            <span className="feature-badge">📡 SNMP Discovery</span>
          )}
        </div>
      </div>

      <div className="template-actions">
        <button 
          onClick={() => setShowDetails(!showDetails)}
          className="btn btn-secondary"
        >
          {showDetails ? '👁️ Hide Details' : '👁️ Show Details'}
        </button>
        <button 
          onClick={handleUseTemplate}
          className="btn btn-primary"
        >
          🚀 Use Template
        </button>
      </div>

      {showDetails && (
        <div className="template-details-expanded">
          <div className="details-section">
            <h5>Network Configuration</h5>
            <div className="network-ranges">
              {template.network_ranges.map((range, index) => (
                <span key={index} className="network-range">{range}</span>
              ))}
            </div>
          </div>

          <div className="details-section">
            <h5>Port Configuration</h5>
            <div className="ports-list">
              {template.common_ports.map(port => (
                <span key={port} className="port-badge">{port}</span>
              ))}
            </div>
          </div>

          <div className="details-section">
            <h5>Settings</h5>
            <div className="settings-grid">
              <div className="setting-item">
                <span className="setting-label">Timeout:</span>
                <span className="setting-value">{template.timeout}s</span>
              </div>
              <div className="setting-item">
                <span className="setting-label">Max Concurrent:</span>
                <span className="setting-value">{template.max_concurrent}</span>
              </div>
              {template.enable_snmp && template.snmp_communities.length > 0 && (
                <div className="setting-item">
                  <span className="setting-label">SNMP Communities:</span>
                  <span className="setting-value">{template.snmp_communities.join(', ')}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Create Template Modal Component
const CreateTemplateModal = ({ onClose, onTemplateCreated }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    network_ranges: [''],
    common_ports: [],
    timeout: 3.0,
    max_concurrent: 100,
    snmp_communities: ['public'],
    enable_snmp: false,
    enable_service_detection: true,
    enable_hostname_resolution: true,
    is_active: true,
    port_preset: 'basic'
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  const portPresets = discoveryService.getCommonPortPresets();

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleNetworkRangeChange = (index, value) => {
    const newRanges = [...formData.network_ranges];
    newRanges[index] = value;
    setFormData(prev => ({
      ...prev,
      network_ranges: newRanges
    }));
  };

  const addNetworkRange = () => {
    setFormData(prev => ({
      ...prev,
      network_ranges: [...prev.network_ranges, '']
    }));
  };

  const removeNetworkRange = (index) => {
    if (formData.network_ranges.length > 1) {
      const newRanges = formData.network_ranges.filter((_, i) => i !== index);
      setFormData(prev => ({
        ...prev,
        network_ranges: newRanges
      }));
    }
  };

  const handlePresetChange = (e) => {
    const preset = e.target.value;
    setFormData(prev => ({
      ...prev,
      port_preset: preset,
      common_ports: preset ? portPresets[preset].ports : []
    }));
  };

  const handleCustomPorts = (e) => {
    const portsStr = e.target.value;
    const ports = portsStr.split(',')
      .map(p => parseInt(p.trim()))
      .filter(p => !isNaN(p) && p >= 1 && p <= 65535);
    
    setFormData(prev => ({
      ...prev,
      common_ports: ports,
      port_preset: ''
    }));
  };

  const handleSNMPCommunities = (e) => {
    const communities = e.target.value.split(',').map(c => c.trim()).filter(c => c);
    setFormData(prev => ({
      ...prev,
      snmp_communities: communities
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Template name is required');
      return;
    }

    const validRanges = formData.network_ranges.filter(range => 
      range.trim() && discoveryService.validateNetworkRange(range.trim())
    );

    if (validRanges.length === 0) {
      setError('At least one valid network range is required');
      return;
    }

    try {
      setCreating(true);
      setError(null);

      const templateData = {
        ...formData,
        network_ranges: validRanges,
        snmp_communities: formData.enable_snmp ? formData.snmp_communities : []
      };

      await discoveryService.createDiscoveryTemplate(templateData);
      onTemplateCreated();
    } catch (err) {
      console.error('Error creating template:', err);
      setError(err.response?.data?.detail || 'Failed to create discovery template');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content create-template-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📋 Create Discovery Template</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <form onSubmit={handleSubmit} className="create-template-form">
            <div className="form-group">
              <label htmlFor="name">Template Name *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Production Network Scan"
                required
                disabled={creating}
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Describe this template..."
                rows="3"
                disabled={creating}
              />
            </div>

            <div className="form-group">
              <label>Network Ranges *</label>
              {formData.network_ranges.map((range, index) => (
                <div key={index} className="network-range-input">
                  <input
                    type="text"
                    value={range}
                    onChange={(e) => handleNetworkRangeChange(index, e.target.value)}
                    placeholder="192.168.1.0/24"
                    disabled={creating}
                  />
                  {formData.network_ranges.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeNetworkRange(index)}
                      className="remove-range-btn"
                      disabled={creating}
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={addNetworkRange}
                className="add-range-btn"
                disabled={creating}
              >
                + Add Network Range
              </button>
            </div>

            <div className="form-group">
              <label htmlFor="port_preset">Port Configuration</label>
              <select
                id="port_preset"
                value={formData.port_preset}
                onChange={handlePresetChange}
                disabled={creating}
              >
                <option value="">Custom Ports</option>
                {Object.entries(portPresets).map(([key, preset]) => (
                  <option key={key} value={key}>{preset.name}</option>
                ))}
              </select>
            </div>

            {formData.port_preset && (
              <div className="form-group">
                <label>Selected Ports</label>
                <div className="port-list">
                  {portPresets[formData.port_preset].ports.join(', ')}
                </div>
              </div>
            )}

            {!formData.port_preset && (
              <div className="form-group">
                <label htmlFor="custom_ports">Custom Ports</label>
                <input
                  type="text"
                  id="custom_ports"
                  placeholder="22, 80, 443, 3389, 5985"
                  onChange={handleCustomPorts}
                  disabled={creating}
                />
                <small>Comma-separated list of ports (1-65535)</small>
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="timeout">Timeout (seconds)</label>
                <input
                  type="number"
                  id="timeout"
                  name="timeout"
                  value={formData.timeout}
                  onChange={handleInputChange}
                  min="0.1"
                  max="30"
                  step="0.1"
                  disabled={creating}
                />
              </div>

              <div className="form-group">
                <label htmlFor="max_concurrent">Max Concurrent</label>
                <input
                  type="number"
                  id="max_concurrent"
                  name="max_concurrent"
                  value={formData.max_concurrent}
                  onChange={handleInputChange}
                  min="1"
                  max="1000"
                  disabled={creating}
                />
              </div>
            </div>

            <div className="form-group">
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="enable_service_detection"
                    checked={formData.enable_service_detection}
                    onChange={handleInputChange}
                    disabled={creating}
                  />
                  <span className="checkmark"></span>
                  Enable Service Detection
                </label>
              </div>
            </div>

            <div className="form-group">
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="enable_hostname_resolution"
                    checked={formData.enable_hostname_resolution}
                    onChange={handleInputChange}
                    disabled={creating}
                  />
                  <span className="checkmark"></span>
                  Enable Hostname Resolution
                </label>
              </div>
            </div>

            <div className="form-group">
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="enable_snmp"
                    checked={formData.enable_snmp}
                    onChange={handleInputChange}
                    disabled={creating}
                  />
                  <span className="checkmark"></span>
                  Enable SNMP Discovery
                </label>
              </div>
            </div>

            {formData.enable_snmp && (
              <div className="form-group">
                <label htmlFor="snmp_communities">SNMP Communities</label>
                <input
                  type="text"
                  id="snmp_communities"
                  value={formData.snmp_communities.join(', ')}
                  onChange={handleSNMPCommunities}
                  placeholder="public, private"
                  disabled={creating}
                />
              </div>
            )}

            <div className="form-group">
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                    disabled={creating}
                  />
                  <span className="checkmark"></span>
                  template is active
                </label>
                <small>active templates appear in the template selection list</small>
              </div>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <div className="form-actions">
              <button type="button" onClick={onClose} disabled={creating}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={creating}>
                {creating ? (
                  <>
                    <span className="spinner"></span>
                    Creating...
                  </>
                ) : (
                  <>
                    📋 Create Template
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default DiscoveryTemplatesTab;