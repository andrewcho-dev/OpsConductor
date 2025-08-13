/**
 * Discovered Devices Tab Component
 * Manages discovered devices with import functionality
 */

import React, { useState, useEffect } from 'react';
import discoveryService from '../../services/discoveryService';

const DiscoveredDevicesTab = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDevices, setSelectedDevices] = useState(new Set());
  const [showImportModal, setShowImportModal] = useState(false);
  const [filters, setFilters] = useState({
    status: '',
    deviceType: '',
    jobId: '',
    search: ''
  });
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    loadDevices();
    loadJobs();
  }, [filters]);

  const loadDevices = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.deviceType) params.deviceType = filters.deviceType;
      if (filters.jobId) params.jobId = filters.jobId;
      
      const devicesData = await discoveryService.getDiscoveredDevices(params);
      
      // Filter by search term if provided
      let filteredDevices = devicesData;
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        filteredDevices = devicesData.filter(device => 
          device.ip_address.includes(searchTerm) ||
          (device.hostname && device.hostname.toLowerCase().includes(searchTerm)) ||
          device.device_type.toLowerCase().includes(searchTerm)
        );
      }
      
      setDevices(filteredDevices);
    } catch (err) {
      console.error('Error loading devices:', err);
      setError('Failed to load discovered devices');
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      const jobsData = await discoveryService.getDiscoveryJobs({ limit: 100 });
      setJobs(jobsData);
    } catch (err) {
      console.error('Error loading jobs:', err);
    }
  };

  const handleDeviceSelect = (deviceId, selected) => {
    const newSelected = new Set(selectedDevices);
    if (selected) {
      newSelected.add(deviceId);
    } else {
      newSelected.delete(deviceId);
    }
    setSelectedDevices(newSelected);
  };

  const handleSelectAll = (selected) => {
    if (selected) {
      setSelectedDevices(new Set(devices.map(d => d.id)));
    } else {
      setSelectedDevices(new Set());
    }
  };

  const handleUpdateDeviceStatus = async (deviceId, status) => {
    try {
      await discoveryService.updateDiscoveredDeviceStatus(deviceId, status);
      loadDevices(); // Refresh list
    } catch (err) {
      console.error('Error updating device status:', err);
      setError('Failed to update device status');
    }
  };

  const handleBulkImport = () => {
    if (selectedDevices.size === 0) {
      setError('Please select devices to import');
      return;
    }
    setShowImportModal(true);
  };

  const handleImportComplete = () => {
    setShowImportModal(false);
    setSelectedDevices(new Set());
    loadDevices(); // Refresh list
  };

  const getUniqueDeviceTypes = () => {
    const types = [...new Set(devices.map(d => d.device_type))];
    return types.sort();
  };

  if (loading) {
    return (
      <div className="devices-tab">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading discovered devices...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="devices-tab">
      {/* Header */}
      <div className="tab-header">
        <div className="header-content">
          <h2>Discovered Devices</h2>
          <p>Review and import discovered network devices</p>
        </div>
        <div className="header-actions">
          {selectedDevices.size > 0 && (
            <button onClick={handleBulkImport} className="btn btn-primary">
              📥 Import Selected ({selectedDevices.size})
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="devices-filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search devices..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="search-input"
          />
        </div>
        <div className="filter-group">
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="status-filter"
          >
            <option value="">All Statuses</option>
            <option value="discovered">Discovered</option>
            <option value="imported">Imported</option>
            <option value="ignored">Ignored</option>
          </select>
        </div>
        <div className="filter-group">
          <select
            value={filters.deviceType}
            onChange={(e) => setFilters(prev => ({ ...prev, deviceType: e.target.value }))}
            className="type-filter"
          >
            <option value="">All Types</option>
            {getUniqueDeviceTypes().map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <select
            value={filters.jobId}
            onChange={(e) => setFilters(prev => ({ ...prev, jobId: e.target.value }))}
            className="job-filter"
          >
            <option value="">All Jobs</option>
            {jobs.map(job => (
              <option key={job.id} value={job.id}>{job.name}</option>
            ))}
          </select>
        </div>
        <button onClick={loadDevices} className="btn btn-secondary">
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Devices List */}
      <div className="devices-list">
        {devices.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📱</div>
            <h3>No Devices Found</h3>
            <p>No devices match your current filters. Try adjusting the filters or run a discovery job.</p>
          </div>
        ) : (
          <>
            {/* Bulk Actions */}
            <div className="bulk-actions">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedDevices.size === devices.length && devices.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
                <span className="checkmark"></span>
                Select All ({devices.length} devices)
              </label>
              {selectedDevices.size > 0 && (
                <span className="selection-info">
                  {selectedDevices.size} device{selectedDevices.size !== 1 ? 's' : ''} selected
                </span>
              )}
            </div>

            {/* Devices Grid */}
            <div className="devices-grid">
              {devices.map(device => (
                <DeviceCard
                  key={device.id}
                  device={device}
                  selected={selectedDevices.has(device.id)}
                  onSelect={(selected) => handleDeviceSelect(device.id, selected)}
                  onUpdateStatus={(status) => handleUpdateDeviceStatus(device.id, status)}
                />
              ))}
            </div>
          </>
        )}
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <ImportDevicesModal
          deviceIds={Array.from(selectedDevices)}
          onClose={() => setShowImportModal(false)}
          onImportComplete={handleImportComplete}
        />
      )}
    </div>
  );
};

// Device Card Component
const DeviceCard = ({ device, selected, onSelect, onUpdateStatus }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className={`device-card ${selected ? 'selected' : ''}`}>
      <div className="device-header">
        <div className="device-select">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={selected}
              onChange={(e) => onSelect(e.target.checked)}
            />
            <span className="checkmark"></span>
          </label>
        </div>
        <div className="device-info">
          <div className="device-icon">
            {discoveryService.getDeviceTypeIcon(device.device_type)}
          </div>
          <div className="device-details">
            <h4>{device.ip_address}</h4>
            {device.hostname && (
              <p className="device-hostname">{device.hostname}</p>
            )}
          </div>
        </div>
        <div className="device-status">
          <span 
            className={`status-badge ${device.status}`}
            style={{ color: discoveryService.getStatusColor(device.status) }}
          >
            {device.status}
          </span>
        </div>
      </div>

      <div className="device-summary">
        <div className="summary-item">
          <span className="summary-label">Type:</span>
          <span 
            className="type-badge"
            style={{ 
              backgroundColor: discoveryService.getDeviceTypeColor(device.device_type),
              color: 'white'
            }}
          >
            {device.device_type}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Confidence:</span>
          <span className="confidence-score">
            {Math.round(device.confidence_score * 100)}%
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Discovered:</span>
          <span className="discovery-time">
            {discoveryService.formatDiscoveryTime(device.discovered_at)}
          </span>
        </div>
      </div>

      {device.open_ports.length > 0 && (
        <div className="device-ports">
          <span className="ports-label">Open Ports:</span>
          <div className="ports-list">
            {device.open_ports.slice(0, 8).map(port => (
              <span key={port} className="port-badge">{port}</span>
            ))}
            {device.open_ports.length > 8 && (
              <span className="port-badge more">+{device.open_ports.length - 8}</span>
            )}
          </div>
        </div>
      )}

      {device.suggested_communication_methods.length > 0 && (
        <div className="device-methods">
          <span className="methods-label">Suggested Methods:</span>
          <div className="methods-list">
            {device.suggested_communication_methods.map(method => (
              <span key={method} className="method-badge">{method}</span>
            ))}
          </div>
        </div>
      )}

      <div className="device-actions">
        <button 
          onClick={() => setShowDetails(!showDetails)}
          className="btn btn-secondary"
        >
          {showDetails ? '👁️ Hide Details' : '👁️ Show Details'}
        </button>
        
        {device.status === 'discovered' && (
          <>
            <button 
              onClick={() => onUpdateStatus('ignored')}
              className="btn btn-warning"
            >
              🚫 Ignore
            </button>
          </>
        )}
        
        {device.status === 'ignored' && (
          <button 
            onClick={() => onUpdateStatus('discovered')}
            className="btn btn-success"
          >
            ↩️ Restore
          </button>
        )}
      </div>

      {showDetails && (
        <div className="device-details-expanded">
          <div className="details-section">
            <h5>Services</h5>
            {Object.keys(device.services).length > 0 ? (
              <div className="services-list">
                {Object.entries(device.services).map(([port, service]) => (
                  <div key={port} className="service-item">
                    <span className="service-port">{port}:</span>
                    <span className="service-name">{service.service || 'unknown'}</span>
                    {service.banner && service.banner !== 'No banner' && (
                      <span className="service-banner">{service.banner}</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-services">No services detected</p>
            )}
          </div>

          {device.mac_address && (
            <div className="details-section">
              <h5>MAC Address</h5>
              <p>{device.mac_address}</p>
            </div>
          )}

          {Object.keys(device.snmp_info).length > 0 && (
            <div className="details-section">
              <h5>SNMP Information</h5>
              <div className="snmp-info">
                {Object.entries(device.snmp_info).map(([key, value]) => (
                  <div key={key} className="snmp-item">
                    <span className="snmp-key">{key}:</span>
                    <span className="snmp-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Import Devices Modal Component
const ImportDevicesModal = ({ deviceIds, onClose, onImportComplete }) => {
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    auto_create_communication_methods: true,
    default_environment: 'development',
    default_credentials: {
      username: '',
      password: ''
    }
  });

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (name.startsWith('credentials.')) {
      const credField = name.split('.')[1];
      setFormData(prev => ({
        ...prev,
        default_credentials: {
          ...prev.default_credentials,
          [credField]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleImport = async (e) => {
    e.preventDefault();
    
    try {
      setImporting(true);
      setError(null);

      const importData = {
        device_ids: deviceIds,
        auto_create_communication_methods: formData.auto_create_communication_methods,
        default_environment: formData.default_environment,
        default_credentials: formData.default_credentials.username ? formData.default_credentials : null
      };

      const result = await discoveryService.importDiscoveredDevices(importData);
      
      if (result.failed_count > 0) {
        setError(`Import completed with ${result.failed_count} failures: ${result.errors.join(', ')}`);
      } else {
        onImportComplete();
      }
    } catch (err) {
      console.error('Error importing devices:', err);
      setError(err.response?.data?.detail || 'Failed to import devices');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content import-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📥 Import Devices</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <form onSubmit={handleImport} className="import-form">
            <div className="form-group">
              <p>Importing {deviceIds.length} device{deviceIds.length !== 1 ? 's' : ''} as targets.</p>
            </div>

            <div className="form-group">
              <label htmlFor="default_environment">Default Environment</label>
              <select
                id="default_environment"
                name="default_environment"
                value={formData.default_environment}
                onChange={handleInputChange}
                disabled={importing}
              >
                <option value="development">Development</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
            </div>

            <div className="form-group">
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="auto_create_communication_methods"
                    checked={formData.auto_create_communication_methods}
                    onChange={handleInputChange}
                    disabled={importing}
                  />
                  <span className="checkmark"></span>
                  Auto-create communication methods
                </label>
                <small>Automatically create communication methods based on detected services</small>
              </div>
            </div>

            <div className="form-group">
              <h4>Default Credentials (Optional)</h4>
              <div className="credentials-group">
                <div className="form-group">
                  <label htmlFor="credentials.username">Username</label>
                  <input
                    type="text"
                    id="credentials.username"
                    name="credentials.username"
                    value={formData.default_credentials.username}
                    onChange={handleInputChange}
                    placeholder="admin"
                    disabled={importing}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="credentials.password">Password</label>
                  <input
                    type="password"
                    id="credentials.password"
                    name="credentials.password"
                    value={formData.default_credentials.password}
                    onChange={handleInputChange}
                    placeholder="Enter password"
                    disabled={importing}
                  />
                </div>
              </div>
              <small>These credentials will be used for all imported devices. You can change them later.</small>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <div className="form-actions">
              <button type="button" onClick={onClose} disabled={importing}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={importing}>
                {importing ? (
                  <>
                    <span className="spinner"></span>
                    Importing...
                  </>
                ) : (
                  <>
                    📥 Import Devices
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

export default DiscoveredDevicesTab;