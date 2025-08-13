/**
 * New Discovery Job Modal
 * Modal for creating new network discovery jobs
 */

import React, { useState, useEffect } from 'react';
import discoveryService from '../../services/discoveryService';

const NewDiscoveryJobModal = ({ isOpen, onClose, onJobCreated }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    network_ranges: [''],
    port_ranges: [],
    common_ports: [],
    timeout: 3.0,
    max_concurrent: 100,
    snmp_communities: ['public'],
    enable_snmp: false,
    enable_service_detection: true,
    enable_hostname_resolution: true,
    port_preset: 'basic'
  });
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1);

  const portPresets = discoveryService.getCommonPortPresets();

  useEffect(() => {
    if (isOpen) {
      loadTemplates();
    }
  }, [isOpen]);

  const loadTemplates = async () => {
    try {
      const templatesData = await discoveryService.getDiscoveryTemplates();
      setTemplates(Array.isArray(templatesData) ? templatesData : []);
    } catch (err) {
      console.error('Error loading templates:', err);
      setTemplates([]); // Ensure templates is always an array
    }
  };

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

  const handleTemplateSelect = async (e) => {
    const templateId = e.target.value;
    setSelectedTemplate(templateId);
    
    if (templateId) {
      try {
        const template = await discoveryService.getDiscoveryTemplate(templateId);
        setFormData({
          name: `${template.name} - ${new Date().toLocaleDateString()}`,
          description: template.description || '',
          network_ranges: template.network_ranges,
          port_ranges: template.port_ranges || [],
          common_ports: template.common_ports || [],
          timeout: template.timeout,
          max_concurrent: template.max_concurrent,
          snmp_communities: template.snmp_communities || ['public'],
          enable_snmp: template.enable_snmp,
          enable_service_detection: template.enable_service_detection,
          enable_hostname_resolution: template.enable_hostname_resolution,
          port_preset: ''
        });
      } catch (err) {
        console.error('Error loading template:', err);
      }
    }
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('Job name is required');
      return false;
    }

    const validRanges = formData.network_ranges.filter(range => 
      range.trim() && discoveryService.validateNetworkRange(range.trim())
    );

    if (validRanges.length === 0) {
      setError('At least one valid network range is required');
      return false;
    }

    if (formData.timeout < 0.1 || formData.timeout > 30) {
      setError('Timeout must be between 0.1 and 30 seconds');
      return false;
    }

    if (formData.max_concurrent < 1 || formData.max_concurrent > 1000) {
      setError('Max concurrent connections must be between 1 and 1000');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setCreating(true);
      setError(null);

      const jobData = {
        ...formData,
        network_ranges: formData.network_ranges.filter(range => range.trim()),
        snmp_communities: formData.enable_snmp ? formData.snmp_communities : []
      };

      const newJob = await discoveryService.createDiscoveryJob(jobData);
      
      if (onJobCreated) {
        onJobCreated(newJob);
      }
      
      handleClose();
    } catch (err) {
      console.error('Error creating discovery job:', err);
      setError(err.response?.data?.detail || 'Failed to create discovery job');
    } finally {
      setCreating(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      network_ranges: [''],
      port_ranges: [],
      common_ports: [],
      timeout: 3.0,
      max_concurrent: 100,
      snmp_communities: ['public'],
      enable_snmp: false,
      enable_service_detection: true,
      enable_hostname_resolution: true,
      port_preset: 'basic'
    });
    setSelectedTemplate('');
    setError(null);
    setStep(1);
    setCreating(false);
    onClose();
  };

  const nextStep = () => {
    if (step === 1) {
      if (!formData.name.trim()) {
        setError('Job name is required');
        return;
      }
      const validRanges = formData.network_ranges.filter(range => 
        range.trim() && discoveryService.validateNetworkRange(range.trim())
      );
      if (validRanges.length === 0) {
        setError('At least one valid network range is required');
        return;
      }
    }
    setError(null);
    setStep(step + 1);
  };

  const prevStep = () => {
    setError(null);
    setStep(step - 1);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content new-job-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>➕ New Discovery Job</h2>
          <button className="modal-close" onClick={handleClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="step-indicator">
            <div className={`step ${step >= 1 ? 'active' : ''}`}>
              <span>1</span>
              <label>Basic Info</label>
            </div>
            <div className={`step ${step >= 2 ? 'active' : ''}`}>
              <span>2</span>
              <label>Network & Ports</label>
            </div>
            <div className={`step ${step >= 3 ? 'active' : ''}`}>
              <span>3</span>
              <label>Options</label>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="new-job-form">
            {step === 1 && (
              <div className="form-step">
                <h3>Basic Information</h3>
                
                {templates && templates.length > 0 && (
                  <div className="form-group">
                    <label htmlFor="template">Start from Template (Optional)</label>
                    <select
                      id="template"
                      value={selectedTemplate}
                      onChange={handleTemplateSelect}
                      disabled={creating}
                    >
                      <option value="">Create from scratch</option>
                      {templates.map(template => (
                        <option key={template.id} value={template.id}>
                          {template.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="name">Job Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Network Discovery - Production"
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
                    placeholder="Describe the purpose of this discovery job..."
                    rows="3"
                    disabled={creating}
                  />
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="form-step">
                <h3>Network Ranges & Ports</h3>
                
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
                  <small>Use CIDR notation (e.g., 192.168.1.0/24, 10.0.0.0/16)</small>
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
              </div>
            )}

            {step === 3 && (
              <div className="form-step">
                <h3>Discovery Options</h3>
                
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
                    <small>Detect services running on open ports (HTTP, SSH, etc.)</small>
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
                    <small>Resolve hostnames for discovered IP addresses</small>
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
                    <small>Use SNMP to gather device information (requires SNMP to be enabled)</small>
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
                    <small>Comma-separated list of SNMP community strings</small>
                  </div>
                )}
              </div>
            )}

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <div className="form-actions">
              <div className="step-navigation">
                {step > 1 && (
                  <button type="button" onClick={prevStep} disabled={creating}>
                    ← Previous
                  </button>
                )}
                {step < 3 ? (
                  <button type="button" onClick={nextStep} disabled={creating}>
                    Next →
                  </button>
                ) : (
                  <button type="submit" className="btn-primary" disabled={creating}>
                    {creating ? (
                      <>
                        <span className="spinner"></span>
                        Creating...
                      </>
                    ) : (
                      <>
                        🚀 Create Job
                      </>
                    )}
                  </button>
                )}
              </div>
              <button type="button" onClick={handleClose} disabled={creating}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewDiscoveryJobModal;