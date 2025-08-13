/**
 * Quick Network Scan Modal
 * Allows users to perform quick network scans without creating full discovery jobs
 */

import React, { useState } from 'react';
import discoveryService from '../../services/discoveryService';

const QuickScanModal = ({ isOpen, onClose, onScanComplete }) => {
  const [formData, setFormData] = useState({
    network_range: '192.168.1.0/24',
    ports: [],
    timeout: 2.0,
    port_preset: 'basic'
  });
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const portPresets = discoveryService.getCommonPortPresets();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePresetChange = (e) => {
    const preset = e.target.value;
    setFormData(prev => ({
      ...prev,
      port_preset: preset,
      ports: preset ? portPresets[preset].ports : []
    }));
  };

  const handleCustomPorts = (e) => {
    const portsStr = e.target.value;
    const ports = portsStr.split(',')
      .map(p => parseInt(p.trim()))
      .filter(p => !isNaN(p) && p >= 1 && p <= 65535);
    
    setFormData(prev => ({
      ...prev,
      ports,
      port_preset: ''
    }));
  };

  const handleScan = async (e) => {
    e.preventDefault();
    
    if (!discoveryService.validateNetworkRange(formData.network_range)) {
      setError('Invalid network range. Please use CIDR notation (e.g., 192.168.1.0/24)');
      return;
    }

    try {
      setScanning(true);
      setError(null);
      setResults(null);

      const scanData = {
        network_range: formData.network_range,
        ports: formData.ports.length > 0 ? formData.ports : undefined,
        timeout: formData.timeout
      };

      const scanResults = await discoveryService.quickNetworkScan(scanData);
      setResults(scanResults);
      
      if (onScanComplete) {
        onScanComplete(scanResults);
      }
    } catch (err) {
      console.error('Quick scan failed:', err);
      setError(err.response?.data?.detail || 'Scan failed. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  const handleClose = () => {
    setFormData({
      network_range: '192.168.1.0/24',
      ports: [],
      timeout: 2.0,
      port_preset: 'basic'
    });
    setResults(null);
    setError(null);
    setScanning(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content quick-scan-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>⚡ Quick Network Scan</h2>
          <button className="modal-close" onClick={handleClose}>×</button>
        </div>

        <div className="modal-body">
          {!results ? (
            <form onSubmit={handleScan} className="quick-scan-form">
              <div className="form-group">
                <label htmlFor="network_range">Network Range</label>
                <input
                  type="text"
                  id="network_range"
                  name="network_range"
                  value={formData.network_range}
                  onChange={handleInputChange}
                  placeholder="192.168.1.0/24"
                  required
                  disabled={scanning}
                />
                <small>Use CIDR notation (e.g., 192.168.1.0/24, 10.0.0.0/16)</small>
              </div>

              <div className="form-group">
                <label htmlFor="port_preset">Port Preset</label>
                <select
                  id="port_preset"
                  value={formData.port_preset}
                  onChange={handlePresetChange}
                  disabled={scanning}
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
                    placeholder="22, 80, 443, 3389"
                    onChange={handleCustomPorts}
                    disabled={scanning}
                  />
                  <small>Comma-separated list of ports (1-65535)</small>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="timeout">Timeout (seconds)</label>
                <input
                  type="number"
                  id="timeout"
                  name="timeout"
                  value={formData.timeout}
                  onChange={handleInputChange}
                  min="0.1"
                  max="10"
                  step="0.1"
                  disabled={scanning}
                />
              </div>

              {error && (
                <div className="error-message">
                  <span className="error-icon">⚠️</span>
                  {error}
                </div>
              )}

              <div className="form-actions">
                <button type="button" onClick={handleClose} disabled={scanning}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={scanning}>
                  {scanning ? (
                    <>
                      <span className="spinner"></span>
                      Scanning...
                    </>
                  ) : (
                    <>
                      🔍 Start Scan
                    </>
                  )}
                </button>
              </div>
            </form>
          ) : (
            <div className="scan-results">
              <div className="results-header">
                <h3>Scan Results</h3>
                <div className="results-summary">
                  <span className="result-stat">
                    📡 Range: {results.network_range}
                  </span>
                  <span className="result-stat">
                    ⏱️ Duration: {results.scan_duration.toFixed(2)}s
                  </span>
                  <span className="result-stat">
                    📱 Found: {results.devices_found.length} devices
                  </span>
                </div>
              </div>

              {results.devices_found.length === 0 ? (
                <div className="no-devices">
                  <div className="no-devices-icon">📭</div>
                  <h4>No Devices Found</h4>
                  <p>No responsive devices were found in the specified network range.</p>
                </div>
              ) : (
                <div className="devices-found">
                  {results.devices_found.map((device, index) => (
                    <div key={index} className="device-result">
                      <div className="device-header">
                        <div className="device-info">
                          <span className="device-icon">
                            {discoveryService.getDeviceTypeIcon(device.device_type)}
                          </span>
                          <div className="device-details">
                            <h4>{device.ip_address}</h4>
                            {device.hostname && (
                              <p className="device-hostname">{device.hostname}</p>
                            )}
                          </div>
                        </div>
                        <div className="device-type">
                          <span 
                            className="type-badge"
                            style={{ 
                              backgroundColor: discoveryService.getDeviceTypeColor(device.device_type),
                              color: 'white'
                            }}
                          >
                            {device.device_type}
                          </span>
                          <span className="confidence">
                            {Math.round(device.confidence_score * 100)}% confidence
                          </span>
                        </div>
                      </div>
                      
                      {device.open_ports.length > 0 && (
                        <div className="device-ports">
                          <strong>Open Ports:</strong>
                          <div className="ports-list">
                            {device.open_ports.map(port => (
                              <span key={port} className="port-badge">{port}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="results-actions">
                <button onClick={() => setResults(null)}>
                  🔄 New Scan
                </button>
                <button className="btn-primary" onClick={handleClose}>
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuickScanModal;