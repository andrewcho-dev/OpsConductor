import React, { useState, useEffect } from 'react';

const NotificationTemplates = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [message, setMessage] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    subject_template: '',
    body_template: '',
    template_type: 'email',
    description: ''
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/notifications/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
      setMessage({ type: 'error', text: 'Failed to load templates' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setMessage(null);

      const response = await fetch('/api/notifications/templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Template created successfully!' });
        setShowCreateForm(false);
        resetForm();
        fetchTemplates();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to create template' });
      }
    } catch (error) {
      console.error('Error creating template:', error);
      setMessage({ type: 'error', text: 'Failed to create template' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setMessage(null);

      const response = await fetch(`/api/notifications/templates/${editingTemplate.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Template updated successfully!' });
        setEditingTemplate(null);
        resetForm();
        fetchTemplates();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to update template' });
      }
    } catch (error) {
      console.error('Error updating template:', error);
      setMessage({ type: 'error', text: 'Failed to update template' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/notifications/templates/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Template deleted successfully!' });
        fetchTemplates();
      } else {
        setMessage({ type: 'error', text: 'Failed to delete template' });
      }
    } catch (error) {
      console.error('Error deleting template:', error);
      setMessage({ type: 'error', text: 'Failed to delete template' });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      subject_template: template.subject_template,
      body_template: template.body_template,
      template_type: template.template_type,
      description: template.description || ''
    });
    setShowCreateForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      subject_template: '',
      body_template: '',
      template_type: 'email',
      description: ''
    });
  };

  const handleCancel = () => {
    setShowCreateForm(false);
    setEditingTemplate(null);
    resetForm();
  };

  if (loading && templates.length === 0) {
    return (
      <div className="text-center">
        <div className="loading-spinner"></div>
        <p>Loading templates...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">📧 Email Templates</h2>
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateForm(true)}
            disabled={showCreateForm}
          >
            Create Template
          </button>
        </div>

        {message && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        {showCreateForm && (
          <div className="card mb-4">
            <div className="card-header">
              <h3 className="card-title">
                {editingTemplate ? 'Edit Template' : 'Create New Template'}
              </h3>
            </div>

            <form onSubmit={editingTemplate ? handleUpdate : handleCreate}>
              <div className="grid grid-2">
                <div className="form-group">
                  <label className="form-label">Template Name</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="form-input"
                    placeholder="e.g., job_failure_alert"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Template Type</label>
                  <select
                    name="template_type"
                    value={formData.template_type}
                    onChange={handleInputChange}
                    className="form-input"
                  >
                    <option value="email">Email</option>
                    <option value="sms">SMS</option>
                    <option value="webhook">Webhook</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="Template description"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Subject Template</label>
                <input
                  type="text"
                  name="subject_template"
                  value={formData.subject_template}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="EnableDRM Alert: {{alert_type}}"
                  required
                />
                <small className="text-sm text-gray-600">
                  Use {'{{variable_name}}'} for dynamic content
                </small>
              </div>

              <div className="form-group">
                <label className="form-label">Body Template</label>
                <textarea
                  name="body_template"
                  value={formData.body_template}
                  onChange={handleInputChange}
                  className="form-input form-textarea"
                  placeholder="Enter your email template body..."
                  required
                />
                <small className="text-sm text-gray-600">
                  Use {'{{variable_name}}'} for dynamic content. Example: {'{{job_name}}'}, {'{{error_message}}'}, {'{{timestamp}}'}
                </small>
              </div>

              <div className="flex gap-3">
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : (editingTemplate ? 'Update Template' : 'Create Template')}
                </button>
                <button type="button" className="btn btn-secondary" onClick={handleCancel}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Subject</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {templates.map((template) => (
                <tr key={template.id}>
                  <td>
                    <div>
                      <strong>{template.name}</strong>
                      {template.description && (
                        <div className="text-sm text-gray-600">{template.description}</div>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-info">{template.template_type}</span>
                  </td>
                  <td>
                    <div className="text-sm">
                      {template.subject_template.length > 50
                        ? `${template.subject_template.substring(0, 50)}...`
                        : template.subject_template}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${template.is_active ? 'badge-success' : 'badge-error'}`}>
                      {template.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleEdit(template)}
                        disabled={showCreateForm}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleDelete(template.id)}
                        disabled={loading}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {templates.length === 0 && !loading && (
          <div className="text-center py-8">
            <p className="text-gray-600">No templates found. Create your first template to get started.</p>
          </div>
        )}
      </div>

      <div className="card mt-4">
        <div className="card-header">
          <h3 className="card-title">📝 Template Variables Guide</h3>
        </div>

        <div className="grid grid-2">
          <div>
            <h4 className="mb-2">Job Variables</h4>
            <ul className="text-sm">
              <li><code>{'{{job_name}}'}</code> - Job name</li>
              <li><code>{'{{job_id}}'}</code> - Job ID</li>
              <li><code>{'{{status}}'}</code> - Job status</li>
              <li><code>{'{{error_message}}'}</code> - Error message</li>
              <li><code>{'{{target_name}}'}</code> - Target name</li>
              <li><code>{'{{started_at}}'}</code> - Job start time</li>
              <li><code>{'{{completed_at}}'}</code> - Job completion time</li>
            </ul>
          </div>

          <div>
            <h4 className="mb-2">Alert Variables</h4>
            <ul className="text-sm">
              <li><code>{'{{alert_type}}'}</code> - Alert type</li>
              <li><code>{'{{severity}}'}</code> - Alert severity</li>
              <li><code>{'{{message}}'}</code> - Alert message</li>
              <li><code>{'{{timestamp}}'}</code> - Alert timestamp</li>
              <li><code>{'{{component}}'}</code> - System component</li>
              <li><code>{'{{context_data}}'}</code> - Additional context</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationTemplates;
