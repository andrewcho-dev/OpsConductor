/**
 * Actions Workspace Modal - Advanced Action Definition with Conditional Logic
 * Comprehensive workspace for defining complex job workflows
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Tooltip,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Checkbox,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Paper,
  Tabs,
  Tab,
  Autocomplete,
  Collapse,
} from '@mui/material';
import {
  Close as CloseIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  DragIndicator as DragIcon,
  PlayArrow as PlayIcon,
  Code as CodeIcon,
  Api as ApiIcon,
  Storage as DatabaseIcon,
  Email as EmailIcon,
  FileCopy as FileIcon,
  Terminal as TerminalIcon,
  Psychology as LogicIcon,
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  ContentCopy as CopyIcon,
  Visibility as PreviewIcon,
  Settings as SettingsIcon,
  Timeline as WorkflowIcon,

  ArrowDownward as ArrowDownIcon,
  ArrowUpward as ArrowUpIcon,
} from '@mui/icons-material';

// Action type definitions
const ACTION_TYPES = {
  command: {
    icon: TerminalIcon,
    label: 'System Command',
    color: 'primary',
    description: 'Execute shell commands on target systems'
  },
  script: {
    icon: CodeIcon,
    label: 'Script Execution',
    color: 'secondary',
    description: 'Run scripts (bash, python, powershell, etc.)'
  },
  api: {
    icon: ApiIcon,
    label: 'REST API Call',
    color: 'info',
    description: 'Make HTTP requests to APIs'
  },
  database: {
    icon: DatabaseIcon,
    label: 'Database Operation',
    color: 'warning',
    description: 'Execute SQL queries or database operations'
  },
  file: {
    icon: FileIcon,
    label: 'File Operation',
    color: 'success',
    description: 'File transfer, copy, move, delete operations'
  },
  email: {
    icon: EmailIcon,
    label: 'Email/Notification',
    color: 'error',
    description: 'Send emails or notifications'
  },
  condition: {
    icon: LogicIcon,
    label: 'Conditional Logic',
    color: 'purple',
    description: 'If/then logic and branching'
  },
  parallel: {
    icon: WorkflowIcon,
    label: 'Parallel Execution',
    color: 'orange',
    description: 'Execute multiple actions simultaneously'
  }
};

const ActionsWorkspaceModal = ({ 
  open, 
  onClose, 
  onActionsConfigured, 
  initialActions = [], 
  selectedTargets = [] 
}) => {
  const [actions, setActions] = useState([]);
  const [selectedAction, setSelectedAction] = useState(null);
  const [editingAction, setEditingAction] = useState(null);
  const [activeTab, setActiveTab] = useState(0); // 0: Workflow, 1: Variables, 2: Settings
  const [variables, setVariables] = useState([]);
  const [workflowSettings, setWorkflowSettings] = useState({
    continueOnError: false,
    parallelExecution: false,
    timeout: 300,
    retryCount: 0,
    retryDelay: 5
  });

  useEffect(() => {
    if (open && initialActions.length > 0) {
      setActions(initialActions);
    }
  }, [open, initialActions]);

  const handleAddAction = (actionType) => {
    const newAction = {
      id: Date.now().toString(),
      type: actionType,
      name: `${ACTION_TYPES[actionType].label} ${actions.length + 1}`,
      order: actions.length + 1,
      enabled: true,
      continueOnError: false,
      timeout: 30,
      conditions: [],
      parameters: getDefaultParameters(actionType),
      targetCompatibility: checkTargetCompatibility(actionType, selectedTargets)
    };
    
    setActions(prev => [...prev, newAction]);
    setEditingAction(newAction);
  };

  const getDefaultParameters = (actionType) => {
    switch (actionType) {
      case 'command':
        return { 
          command: '', 
          workingDirectory: '', 
          environment: {},
          expectedExitCodes: [0]
        };
      case 'script':
        return { 
          scriptType: 'bash', 
          scriptContent: '', 
          arguments: [],
          workingDirectory: ''
        };
      case 'api':
        return { 
          method: 'GET', 
          url: '', 
          headers: {}, 
          body: '',
          expectedStatusCodes: [200]
        };
      case 'database':
        return { 
          connectionString: '', 
          query: '', 
          queryType: 'SELECT',
          parameters: {}
        };
      case 'file':
        return { 
          operation: 'copy', 
          source: '', 
          destination: '',
          preservePermissions: true
        };
      case 'email':
        return { 
          to: '', 
          subject: '', 
          body: '',
          attachments: []
        };
      case 'condition':
        return { 
          conditionType: 'if', 
          expression: '', 
          trueActions: [],
          falseActions: []
        };
      case 'parallel':
        return { 
          parallelActions: [],
          waitForAll: true,
          maxConcurrency: 5
        };
      default:
        return {};
    }
  };

  const checkTargetCompatibility = (actionType, targets) => {
    // This would check target OS, capabilities, etc.
    // For now, return a simple compatibility score
    return {
      compatible: targets.length > 0,
      warnings: [],
      suggestions: []
    };
  };

  const handleDeleteAction = (actionId) => {
    setActions(prev => prev.filter(action => action.id !== actionId));
    if (editingAction?.id === actionId) {
      setEditingAction(null);
    }
  };

  const handleMoveAction = (actionId, direction) => {
    setActions(prev => {
      const index = prev.findIndex(a => a.id === actionId);
      if (index === -1) return prev;
      
      const newIndex = direction === 'up' ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= prev.length) return prev;
      
      const newActions = [...prev];
      [newActions[index], newActions[newIndex]] = [newActions[newIndex], newActions[index]];
      
      // Update order numbers
      newActions.forEach((action, idx) => {
        action.order = idx + 1;
      });
      
      return newActions;
    });
  };

  const handleActionUpdate = (updatedAction) => {
    setActions(prev => prev.map(action => 
      action.id === updatedAction.id ? updatedAction : action
    ));
  };

  const handleSaveActions = () => {
    const processedActions = actions.map((action, index) => ({
      ...action,
      action_order: index + 1,
      action_type: action.type,
      action_name: action.name,
      action_parameters: action.parameters
    }));
    
    onActionsConfigured(processedActions);
  };

  const renderActionCard = (action) => {
    const ActionIcon = ACTION_TYPES[action.type]?.icon || TerminalIcon;
    const isEditing = editingAction?.id === action.id;
    
    return (
      <Card 
        key={action.id}
        variant="outlined"
        sx={{ 
          mb: 1,
          border: isEditing ? 2 : 1,
          borderColor: isEditing ? 'primary.main' : 'grey.300',
          bgcolor: action.enabled ? 'background.paper' : 'grey.50'
        }}
      >
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DragIcon sx={{ color: 'grey.400', cursor: 'grab' }} />
            <ActionIcon 
              sx={{ 
                color: `${ACTION_TYPES[action.type]?.color || 'primary'}.main`,
                fontSize: 20 
              }} 
            />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {action.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {ACTION_TYPES[action.type]?.description}
              </Typography>
            </Box>
            
            {/* Status indicators */}
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              {!action.enabled && (
                <Chip label="Disabled" size="small" color="default" />
              )}
              {action.targetCompatibility?.warnings?.length > 0 && (
                <Tooltip title="Target compatibility warnings">
                  <WarningIcon sx={{ color: 'warning.main', fontSize: 16 }} />
                </Tooltip>
              )}
              {action.conditions?.length > 0 && (
                <Tooltip title="Has conditions">
                  <LogicIcon sx={{ color: 'purple.main', fontSize: 16 }} />
                </Tooltip>
              )}
            </Box>
          </Box>
          
          {/* Action summary */}
          <Box sx={{ mt: 1, ml: 4 }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              {renderActionSummary(action)}
            </Typography>
          </Box>
        </CardContent>
        
        <CardActions sx={{ py: 0.5, px: 2, justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton 
              size="small" 
              onClick={() => handleMoveAction(action.id, 'up')}
              disabled={action.order === 1}
            >
              <ArrowUpIcon fontSize="small" />
            </IconButton>
            <IconButton 
              size="small" 
              onClick={() => handleMoveAction(action.id, 'down')}
              disabled={action.order === actions.length}
            >
              <ArrowDownIcon fontSize="small" />
            </IconButton>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton 
              size="small" 
              onClick={() => setEditingAction(action)}
              color="primary"
            >
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton 
              size="small" 
              onClick={() => {
                const newAction = { ...action, id: Date.now().toString() };
                setActions(prev => [...prev, newAction]);
              }}
            >
              <CopyIcon fontSize="small" />
            </IconButton>
            <IconButton 
              size="small" 
              onClick={() => handleDeleteAction(action.id)}
              color="error"
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        </CardActions>
      </Card>
    );
  };

  const renderActionSummary = (action) => {
    let summary = '';
    
    switch (action.type) {
      case 'command':
        summary = action.parameters.command || 'No command specified';
        break;
      case 'script':
        summary = `${action.parameters.scriptType} script`;
        if (action.parameters.scriptContent) {
          const lines = action.parameters.scriptContent.split('\n');
          summary += `: ${lines[0].substring(0, 30)}${lines[0].length > 30 ? '...' : ''}`;
        }
        break;
      case 'api':
        summary = `${action.parameters.method} ${action.parameters.url || 'No URL'}`;
        break;
      case 'database':
        summary = `${action.parameters.queryType} query`;
        if (action.parameters.query) {
          summary += `: ${action.parameters.query.substring(0, 30)}${action.parameters.query.length > 30 ? '...' : ''}`;
        }
        break;
      case 'file':
        summary = `${action.parameters.operation}: ${action.parameters.source} → ${action.parameters.destination}`;
        break;
      case 'email':
        summary = `To: ${action.parameters.to}`;
        if (action.parameters.subject) {
          summary += ` | Subject: ${action.parameters.subject}`;
        }
        break;
      case 'condition':
        summary = `If ${action.parameters.expression || 'condition not set'}`;
        break;
      case 'parallel':
        summary = `${action.parameters.parallelActions?.length || 0} parallel actions`;
        break;
      default:
        summary = 'Action configuration needed';
    }
    
    // Add conditional logic indicators
    const indicators = [];
    if (action.conditions?.length > 0) {
      indicators.push(`${action.conditions.length} condition${action.conditions.length > 1 ? 's' : ''}`);
    }
    if (action.dependencies?.length > 0) {
      indicators.push(`${action.dependencies.length} dependenc${action.dependencies.length > 1 ? 'ies' : 'y'}`);
    }
    if (action.retryCount > 0) {
      indicators.push(`${action.retryCount} retries`);
    }
    
    if (indicators.length > 0) {
      summary += ` | ${indicators.join(', ')}`;
    }
    
    return summary;
  };

  const renderActionPalette = () => (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <AddIcon />
        Action Types
      </Typography>
      
      <Grid container spacing={1}>
        {Object.entries(ACTION_TYPES).map(([type, config]) => {
          const Icon = config.icon;
          return (
            <Grid item xs={12} key={type}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Icon />}
                onClick={() => handleAddAction(type)}
                sx={{
                  justifyContent: 'flex-start',
                  textAlign: 'left',
                  py: 1,
                  borderColor: `${config.color}.main`,
                  color: `${config.color}.main`,
                  '&:hover': {
                    bgcolor: `${config.color}.50`,
                    borderColor: `${config.color}.main`
                  }
                }}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {config.label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {config.description}
                  </Typography>
                </Box>
              </Button>
            </Grid>
          );
        })}
      </Grid>
    </Paper>
  );

  const renderWorkflowView = () => (
    <Grid container spacing={2} sx={{ height: '100%' }}>
      {/* Left Panel - Action Palette */}
      <Grid item xs={3}>
        {renderActionPalette()}
      </Grid>
      
      {/* Center Panel - Action Sequence */}
      <Grid item xs={6}>
        <Paper sx={{ p: 2, height: '100%' }}>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <WorkflowIcon />
            Action Sequence ({actions.length})
          </Typography>
          
          {actions.length === 0 ? (
            <Alert severity="info">
              No actions defined. Add actions from the palette on the left.
            </Alert>
          ) : (
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {actions.map(renderActionCard)}
            </Box>
          )}
        </Paper>
      </Grid>
      
      {/* Right Panel - Action Configuration */}
      <Grid item xs={3}>
        <Paper sx={{ p: 2, height: '100%' }}>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <SettingsIcon />
            Configuration
          </Typography>
          
          {editingAction ? (
            <ActionConfigurationPanel 
              action={editingAction}
              onUpdate={handleActionUpdate}
              selectedTargets={selectedTargets}
            />
          ) : (
            <Alert severity="info">
              Select an action to configure its settings.
            </Alert>
          )}
        </Paper>
      </Grid>
    </Grid>
  );

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="xl" 
      fullWidth
      PaperProps={{ sx: { height: '90vh' } }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WorkflowIcon />
          Actions Workspace
          <Chip 
            label={`${actions.length} actions`} 
            size="small" 
            color="primary" 
            variant="outlined" 
          />
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0 }}>
        <Box sx={{ height: '100%' }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Workflow Designer" />
            <Tab label="Variables" />
            <Tab label="Settings" />
          </Tabs>
          
          <Box sx={{ p: 2, height: 'calc(100% - 48px)' }}>
            {activeTab === 0 && renderWorkflowView()}
            {activeTab === 1 && <VariablesPanel variables={variables} setVariables={setVariables} />}
            {activeTab === 2 && <SettingsPanel settings={workflowSettings} setSettings={setWorkflowSettings} actions={actions} />}
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleSaveActions} 
          variant="contained" 
          startIcon={<CheckIcon />}
          disabled={actions.length === 0}
        >
          Apply Actions ({actions.length})
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Action Configuration Panel Component
const ActionConfigurationPanel = ({ action, onUpdate, selectedTargets }) => {
  const [localAction, setLocalAction] = useState(action);

  useEffect(() => {
    // Initialize action with default parameters if they don't exist
    const initializedAction = {
      ...action,
      parameters: {
        ...action.parameters,
        // Set default captureOutput to true for backward compatibility if not set
        captureOutput: action.parameters?.captureOutput !== undefined ? action.parameters.captureOutput : true
      }
    };
    setLocalAction(initializedAction);
    
    // If we added default parameters, update the parent
    if (action.parameters?.captureOutput === undefined) {
      onUpdate(initializedAction);
    }
  }, [action, onUpdate]);

  const handleParameterChange = (key, value) => {
    const updatedAction = {
      ...localAction,
      parameters: {
        ...localAction.parameters,
        [key]: value
      }
    };
    setLocalAction(updatedAction);
    onUpdate(updatedAction);
  };

  const renderParameterFields = () => {
    switch (action.type) {
      case 'command':
        return (
          <>
            <TextField
              fullWidth
              label="Command"
              value={localAction.parameters.command || ''}
              onChange={(e) => handleParameterChange('command', e.target.value)}
              multiline
              rows={3}
              sx={{ mb: 2 }}
              placeholder="ls -la, systemctl status nginx, etc."
            />
            <TextField
              fullWidth
              label="Working Directory"
              value={localAction.parameters.workingDirectory || ''}
              onChange={(e) => handleParameterChange('workingDirectory', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="/home/user, /var/log, etc."
            />
            <TextField
              fullWidth
              label="Expected Exit Codes (comma-separated)"
              value={localAction.parameters.expectedExitCodes?.join(', ') || '0'}
              onChange={(e) => handleParameterChange('expectedExitCodes', e.target.value.split(',').map(c => parseInt(c.trim())).filter(c => !isNaN(c)))}
              sx={{ mb: 2 }}
              placeholder="0, 1, 2"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={localAction.parameters.captureOutput === true}
                  onChange={(e) => handleParameterChange('captureOutput', e.target.checked)}
                />
              }
              label="Capture command output (stdout/stderr)"
              sx={{ mb: 2 }}
            />
          </>
        );
      
      case 'script':
        return (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Script Type</InputLabel>
              <Select
                value={localAction.parameters.scriptType || 'bash'}
                label="Script Type"
                onChange={(e) => handleParameterChange('scriptType', e.target.value)}
              >
                <MenuItem value="bash">Bash</MenuItem>
                <MenuItem value="python">Python</MenuItem>
                <MenuItem value="powershell">PowerShell</MenuItem>
                <MenuItem value="batch">Batch</MenuItem>
                <MenuItem value="javascript">JavaScript (Node.js)</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Script Content"
              value={localAction.parameters.scriptContent || ''}
              onChange={(e) => handleParameterChange('scriptContent', e.target.value)}
              multiline
              rows={6}
              sx={{ mb: 2 }}
              placeholder="#!/bin/bash\necho 'Hello World'"
            />
            <TextField
              fullWidth
              label="Arguments (comma-separated)"
              value={localAction.parameters.arguments?.join(', ') || ''}
              onChange={(e) => handleParameterChange('arguments', e.target.value.split(',').map(a => a.trim()).filter(a => a))}
              sx={{ mb: 2 }}
              placeholder="--verbose, --config=/path/to/config"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={localAction.parameters.captureOutput === true}
                  onChange={(e) => handleParameterChange('captureOutput', e.target.checked)}
                />
              }
              label="Capture script output (stdout/stderr)"
              sx={{ mb: 2 }}
            />
          </>
        );
      
      case 'api':
        return (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Method</InputLabel>
              <Select
                value={localAction.parameters.method || 'GET'}
                label="Method"
                onChange={(e) => handleParameterChange('method', e.target.value)}
              >
                <MenuItem value="GET">GET</MenuItem>
                <MenuItem value="POST">POST</MenuItem>
                <MenuItem value="PUT">PUT</MenuItem>
                <MenuItem value="DELETE">DELETE</MenuItem>
                <MenuItem value="PATCH">PATCH</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="URL"
              value={localAction.parameters.url || ''}
              onChange={(e) => handleParameterChange('url', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="https://api.example.com/endpoint"
            />
            <TextField
              fullWidth
              label="Headers (JSON format)"
              value={JSON.stringify(localAction.parameters.headers || {}, null, 2)}
              onChange={(e) => {
                try {
                  handleParameterChange('headers', JSON.parse(e.target.value));
                } catch (err) {
                  // Invalid JSON, don't update
                }
              }}
              multiline
              rows={3}
              sx={{ mb: 2 }}
              placeholder='{"Authorization": "Bearer ${TOKEN}", "Content-Type": "application/json"}'
            />
            <TextField
              fullWidth
              label="Request Body (JSON format)"
              value={typeof localAction.parameters.body === 'string' ? localAction.parameters.body : JSON.stringify(localAction.parameters.body || {}, null, 2)}
              onChange={(e) => handleParameterChange('body', e.target.value)}
              multiline
              rows={3}
              sx={{ mb: 2 }}
              placeholder='{"key": "value", "status": "active"}'
            />
          </>
        );
      
      case 'database':
        return (
          <>
            <TextField
              fullWidth
              label="Connection String"
              value={localAction.parameters.connectionString || ''}
              onChange={(e) => handleParameterChange('connectionString', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="postgresql://user:pass@host:5432/db"
            />
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Query Type</InputLabel>
              <Select
                value={localAction.parameters.queryType || 'SELECT'}
                label="Query Type"
                onChange={(e) => handleParameterChange('queryType', e.target.value)}
              >
                <MenuItem value="SELECT">SELECT</MenuItem>
                <MenuItem value="INSERT">INSERT</MenuItem>
                <MenuItem value="UPDATE">UPDATE</MenuItem>
                <MenuItem value="DELETE">DELETE</MenuItem>
                <MenuItem value="STORED_PROCEDURE">Stored Procedure</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="SQL Query"
              value={localAction.parameters.query || ''}
              onChange={(e) => handleParameterChange('query', e.target.value)}
              multiline
              rows={4}
              sx={{ mb: 2 }}
              placeholder="SELECT * FROM users WHERE active = true"
            />
          </>
        );
      
      case 'file':
        return (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Operation</InputLabel>
              <Select
                value={localAction.parameters.operation || 'copy'}
                label="Operation"
                onChange={(e) => handleParameterChange('operation', e.target.value)}
              >
                <MenuItem value="copy">Copy</MenuItem>
                <MenuItem value="move">Move</MenuItem>
                <MenuItem value="delete">Delete</MenuItem>
                <MenuItem value="chmod">Change Permissions</MenuItem>
                <MenuItem value="chown">Change Owner</MenuItem>
                <MenuItem value="mkdir">Create Directory</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Source Path"
              value={localAction.parameters.source || ''}
              onChange={(e) => handleParameterChange('source', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="/path/to/source/file"
            />
            <TextField
              fullWidth
              label="Destination Path"
              value={localAction.parameters.destination || ''}
              onChange={(e) => handleParameterChange('destination', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="/path/to/destination/file"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={localAction.parameters.preservePermissions || false}
                  onChange={(e) => handleParameterChange('preservePermissions', e.target.checked)}
                />
              }
              label="Preserve Permissions"
              sx={{ mb: 2 }}
            />
          </>
        );
      
      case 'email':
        return (
          <>
            <TextField
              fullWidth
              label="To (comma-separated emails)"
              value={localAction.parameters.to || ''}
              onChange={(e) => handleParameterChange('to', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="user@example.com, admin@company.com"
            />
            <TextField
              fullWidth
              label="Subject"
              value={localAction.parameters.subject || ''}
              onChange={(e) => handleParameterChange('subject', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="Job Execution Report"
            />
            <TextField
              fullWidth
              label="Email Body"
              value={localAction.parameters.body || ''}
              onChange={(e) => handleParameterChange('body', e.target.value)}
              multiline
              rows={4}
              sx={{ mb: 2 }}
              placeholder="Job completed successfully. Details: ${JOB_RESULT}"
            />
          </>
        );
      
      case 'condition':
        return (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Condition Type</InputLabel>
              <Select
                value={localAction.parameters.conditionType || 'if'}
                label="Condition Type"
                onChange={(e) => handleParameterChange('conditionType', e.target.value)}
              >
                <MenuItem value="if">If/Then</MenuItem>
                <MenuItem value="switch">Switch/Case</MenuItem>
                <MenuItem value="while">While Loop</MenuItem>
                <MenuItem value="for">For Loop</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Condition Expression"
              value={localAction.parameters.expression || ''}
              onChange={(e) => handleParameterChange('expression', e.target.value)}
              sx={{ mb: 2 }}
              placeholder="${PREVIOUS_ACTION_EXIT_CODE} == 0"
            />
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Available Variables:</strong><br/>
                • ${`{PREVIOUS_ACTION_EXIT_CODE}`} - Exit code of previous action<br/>
                • ${`{PREVIOUS_ACTION_OUTPUT}`} - Output of previous action<br/>
                • ${`{TARGET_OS}`} - Operating system of target<br/>
                • ${`{JOB_NAME}`} - Name of current job<br/>
                • ${`{EXECUTION_ID}`} - Unique execution ID
              </Typography>
            </Alert>
          </>
        );
      
      case 'parallel':
        return (
          <>
            <TextField
              fullWidth
              type="number"
              label="Max Concurrency"
              value={localAction.parameters.maxConcurrency || 5}
              onChange={(e) => handleParameterChange('maxConcurrency', parseInt(e.target.value))}
              sx={{ mb: 2 }}
              inputProps={{ min: 1, max: 20 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={localAction.parameters.waitForAll || true}
                  onChange={(e) => handleParameterChange('waitForAll', e.target.checked)}
                />
              }
              label="Wait for all parallel actions to complete"
              sx={{ mb: 2 }}
            />
            <Alert severity="info">
              Parallel actions will be configured in the main workflow designer.
            </Alert>
          </>
        );
      
      default:
        return (
          <Alert severity="info">
            Configuration panel for {action.type} actions is ready for use.
          </Alert>
        );
    }
  };

  return (
    <Box>
      <TextField
        fullWidth
        label="Action Name"
        value={localAction.name}
        onChange={(e) => setLocalAction(prev => ({ ...prev, name: e.target.value }))}
        sx={{ mb: 2 }}
      />
      
      <FormControlLabel
        control={
          <Switch
            checked={localAction.enabled}
            onChange={(e) => setLocalAction(prev => ({ ...prev, enabled: e.target.checked }))}
          />
        }
        label="Enabled"
        sx={{ mb: 2 }}
      />
      
      {renderParameterFields()}
      
      <TextField
        fullWidth
        type="number"
        label="Timeout (seconds)"
        value={localAction.timeout || 30}
        onChange={(e) => setLocalAction(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
        sx={{ mb: 2 }}
      />
      
      <FormControlLabel
        control={
          <Switch
            checked={localAction.continueOnError}
            onChange={(e) => setLocalAction(prev => ({ ...prev, continueOnError: e.target.checked }))}
          />
        }
        label="Continue on Error"
        sx={{ mb: 2 }}
      />
      
      {/* Advanced Conditional Logic */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            🔀 Conditional Logic ({localAction.conditions?.length || 0} conditions)
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            Define conditions that must be met for this action to execute.
          </Typography>
          
          {localAction.conditions?.map((condition, index) => (
            <Card key={index} variant="outlined" sx={{ mb: 2, p: 2 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Variable</InputLabel>
                    <Select
                      value={condition.variable || ''}
                      label="Variable"
                      onChange={(e) => {
                        const newConditions = [...(localAction.conditions || [])];
                        newConditions[index] = { ...condition, variable: e.target.value };
                        setLocalAction(prev => ({ ...prev, conditions: newConditions }));
                      }}
                    >
                      <MenuItem value="PREVIOUS_ACTION_EXIT_CODE">Previous Exit Code</MenuItem>
                      <MenuItem value="PREVIOUS_ACTION_OUTPUT">Previous Output</MenuItem>
                      <MenuItem value="TARGET_OS">Target OS</MenuItem>
                      <MenuItem value="TARGET_HOSTNAME">Target Hostname</MenuItem>
                      <MenuItem value="JOB_NAME">Job Name</MenuItem>
                      <MenuItem value="EXECUTION_TIME">Execution Time</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={2}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Operator</InputLabel>
                    <Select
                      value={condition.operator || '=='}
                      label="Operator"
                      onChange={(e) => {
                        const newConditions = [...(localAction.conditions || [])];
                        newConditions[index] = { ...condition, operator: e.target.value };
                        setLocalAction(prev => ({ ...prev, conditions: newConditions }));
                      }}
                    >
                      <MenuItem value="==">=== (equals)</MenuItem>
                      <MenuItem value="!=">=!= (not equals)</MenuItem>
                      <MenuItem value=">">&gt; (greater than)</MenuItem>
                      <MenuItem value="<">&lt; (less than)</MenuItem>
                      <MenuItem value="contains">contains</MenuItem>
                      <MenuItem value="matches">matches regex</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={5}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Value"
                    value={condition.value || ''}
                    onChange={(e) => {
                      const newConditions = [...(localAction.conditions || [])];
                      newConditions[index] = { ...condition, value: e.target.value };
                      setLocalAction(prev => ({ ...prev, conditions: newConditions }));
                    }}
                    placeholder="0, linux, success, etc."
                  />
                </Grid>
                <Grid item xs={2}>
                  <IconButton
                    size="small"
                    onClick={() => {
                      const newConditions = localAction.conditions?.filter((_, i) => i !== index) || [];
                      setLocalAction(prev => ({ ...prev, conditions: newConditions }));
                    }}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Grid>
              </Grid>
            </Card>
          ))}
          
          <Button
            startIcon={<AddIcon />}
            onClick={() => {
              const newCondition = { variable: '', operator: '==', value: '' };
              setLocalAction(prev => ({ 
                ...prev, 
                conditions: [...(prev.conditions || []), newCondition] 
              }));
            }}
            variant="outlined"
            size="small"
          >
            Add Condition
          </Button>
        </AccordionDetails>
      </Accordion>
      
      {/* Action Dependencies */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            🔗 Dependencies ({localAction.dependencies?.length || 0} dependencies)
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            Define which actions must complete successfully before this action can run.
          </Typography>
          
          {localAction.dependencies?.map((dep, index) => (
            <Card key={index} variant="outlined" sx={{ mb: 2, p: 2 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Action Name/ID"
                    value={dep.actionId || ''}
                    onChange={(e) => {
                      const newDeps = [...(localAction.dependencies || [])];
                      newDeps[index] = { ...dep, actionId: e.target.value };
                      setLocalAction(prev => ({ ...prev, dependencies: newDeps }));
                    }}
                    placeholder="Action 1, system-check, etc."
                  />
                </Grid>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Required Status</InputLabel>
                    <Select
                      value={dep.status || 'success'}
                      label="Required Status"
                      onChange={(e) => {
                        const newDeps = [...(localAction.dependencies || [])];
                        newDeps[index] = { ...dep, status: e.target.value };
                        setLocalAction(prev => ({ ...prev, dependencies: newDeps }));
                      }}
                    >
                      <MenuItem value="success">Success</MenuItem>
                      <MenuItem value="failure">Failure</MenuItem>
                      <MenuItem value="completed">Completed (any status)</MenuItem>
                      <MenuItem value="skipped">Skipped</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={2}>
                  <IconButton
                    size="small"
                    onClick={() => {
                      const newDeps = localAction.dependencies?.filter((_, i) => i !== index) || [];
                      setLocalAction(prev => ({ ...prev, dependencies: newDeps }));
                    }}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Grid>
              </Grid>
            </Card>
          ))}
          
          <Button
            startIcon={<AddIcon />}
            onClick={() => {
              const newDep = { actionId: '', status: 'success' };
              setLocalAction(prev => ({ 
                ...prev, 
                dependencies: [...(prev.dependencies || []), newDep] 
              }));
            }}
            variant="outlined"
            size="small"
          >
            Add Dependency
          </Button>
        </AccordionDetails>
      </Accordion>
      
      {/* Retry Logic */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            🔄 Retry & Error Handling
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                size="small"
                label="Retry Count"
                value={localAction.retryCount || 0}
                onChange={(e) => setLocalAction(prev => ({ ...prev, retryCount: parseInt(e.target.value) }))}
                inputProps={{ min: 0, max: 10 }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                size="small"
                label="Retry Delay (seconds)"
                value={localAction.retryDelay || 5}
                onChange={(e) => setLocalAction(prev => ({ ...prev, retryDelay: parseInt(e.target.value) }))}
                inputProps={{ min: 1, max: 300 }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>On Failure Action</InputLabel>
                <Select
                  value={localAction.onFailureAction || 'stop'}
                  label="On Failure Action"
                  onChange={(e) => setLocalAction(prev => ({ ...prev, onFailureAction: e.target.value }))}
                >
                  <MenuItem value="stop">Stop Workflow</MenuItem>
                  <MenuItem value="continue">Continue to Next Action</MenuItem>
                  <MenuItem value="skip_remaining">Skip Remaining Actions</MenuItem>
                  <MenuItem value="rollback">Execute Rollback Actions</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Variables Panel Component
const VariablesPanel = ({ variables, setVariables }) => {
  const handleAddVariable = () => {
    setVariables(prev => [...prev, { key: '', value: '', description: '', type: 'string' }]);
  };

  const predefinedVariables = [
    { key: 'JOB_NAME', description: 'Name of the current job', type: 'system' },
    { key: 'EXECUTION_ID', description: 'Unique execution identifier', type: 'system' },
    { key: 'TARGET_HOST', description: 'Current target hostname', type: 'system' },
    { key: 'TARGET_OS', description: 'Target operating system', type: 'system' },
    { key: 'EXECUTION_TIME', description: 'Job execution start time', type: 'system' },
    { key: 'PREVIOUS_ACTION_EXIT_CODE', description: 'Exit code of previous action', type: 'runtime' },
    { key: 'PREVIOUS_ACTION_OUTPUT', description: 'Output of previous action', type: 'runtime' },
  ];

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Workflow Variables
      </Typography>
      
      {/* System Variables */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" sx={{ mb: 2, color: 'primary.main' }}>
            🔧 System Variables (Read-only)
          </Typography>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            These variables are automatically available in all actions:
          </Typography>
          
          {predefinedVariables.map((variable, index) => (
            <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                ${`{${variable.key}}`}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {variable.description}
              </Typography>
            </Box>
          ))}
        </CardContent>
      </Card>
      
      {/* Custom Variables */}
      <Typography variant="subtitle2" sx={{ mb: 2, color: 'secondary.main' }}>
        📝 Custom Variables
      </Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        Define custom variables that can be used across all actions using ${`{VARIABLE_NAME}`} syntax.
      </Alert>
      
      {variables.map((variable, index) => (
        <Card key={index} variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={3}>
                <TextField
                  fullWidth
                  label="Variable Name"
                  value={variable.key}
                  onChange={(e) => {
                    const newVars = [...variables];
                    newVars[index].key = e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '_');
                    setVariables(newVars);
                  }}
                  placeholder="MY_VARIABLE"
                />
              </Grid>
              <Grid item xs={2}>
                <FormControl fullWidth>
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={variable.type || 'string'}
                    label="Type"
                    onChange={(e) => {
                      const newVars = [...variables];
                      newVars[index].type = e.target.value;
                      setVariables(newVars);
                    }}
                  >
                    <MenuItem value="string">String</MenuItem>
                    <MenuItem value="number">Number</MenuItem>
                    <MenuItem value="boolean">Boolean</MenuItem>
                    <MenuItem value="json">JSON</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={3}>
                <TextField
                  fullWidth
                  label="Default Value"
                  value={variable.value}
                  onChange={(e) => {
                    const newVars = [...variables];
                    newVars[index].value = e.target.value;
                    setVariables(newVars);
                  }}
                  placeholder="default value"
                />
              </Grid>
              <Grid item xs={3}>
                <TextField
                  fullWidth
                  label="Description"
                  value={variable.description}
                  onChange={(e) => {
                    const newVars = [...variables];
                    newVars[index].description = e.target.value;
                    setVariables(newVars);
                  }}
                  placeholder="Variable description"
                />
              </Grid>
              <Grid item xs={1}>
                <IconButton
                  onClick={() => setVariables(prev => prev.filter((_, i) => i !== index))}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Grid>
            </Grid>
            
            {/* Variable Preview */}
            <Box sx={{ mt: 2, p: 1, bgcolor: 'info.50', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'info.dark' }}>
                Usage: ${`{${variable.key || 'VARIABLE_NAME'}}`}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      ))}
      
      <Button
        startIcon={<AddIcon />}
        onClick={handleAddVariable}
        variant="outlined"
      >
        Add Custom Variable
      </Button>
      
      {/* Variable Usage Examples */}
      <Card variant="outlined" sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" sx={{ mb: 2, color: 'success.main' }}>
            💡 Usage Examples
          </Typography>
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Command:</strong> echo "Job ${`{JOB_NAME}`} running on ${`{TARGET_HOST}`}"
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>API URL:</strong> https://api.example.com/jobs/${`{EXECUTION_ID}`}/status
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>File Path:</strong> /logs/${`{JOB_NAME}`}_${`{EXECUTION_TIME}`}.log
            </Typography>
            <Typography variant="body2">
              <strong>Condition:</strong> ${`{PREVIOUS_ACTION_EXIT_CODE}`} == 0
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

// Settings Panel Component
const SettingsPanel = ({ settings, setSettings, actions = [] }) => {
  const validateWorkflow = () => {
    const issues = [];
    
    // Check for actions without configuration
    const unconfiguredActions = actions.filter(action => {
      switch (action.type) {
        case 'command':
          return !action.parameters?.command;
        case 'script':
          return !action.parameters?.scriptContent;
        case 'api':
          return !action.parameters?.url;
        case 'database':
          return !action.parameters?.query;
        case 'file':
          return !action.parameters?.source || !action.parameters?.destination;
        case 'email':
          return !action.parameters?.to;
        default:
          return false;
      }
    });
    
    if (unconfiguredActions.length > 0) {
      issues.push(`${unconfiguredActions.length} action(s) need configuration`);
    }
    
    // Check for circular dependencies
    const checkCircularDeps = (actionId, visited = new Set()) => {
      if (visited.has(actionId)) return true;
      visited.add(actionId);
      
      const action = actions.find(a => a.id === actionId);
      if (action?.dependencies) {
        for (const dep of action.dependencies) {
          if (checkCircularDeps(dep.actionId, new Set(visited))) {
            return true;
          }
        }
      }
      return false;
    };
    
    const circularDeps = actions.filter(action => checkCircularDeps(action.id));
    if (circularDeps.length > 0) {
      issues.push('Circular dependencies detected');
    }
    
    // Check for missing dependencies
    const allActionIds = actions.map(a => a.id);
    const missingDeps = actions.filter(action => 
      action.dependencies?.some(dep => !allActionIds.includes(dep.actionId))
    );
    
    if (missingDeps.length > 0) {
      issues.push('Some actions reference non-existent dependencies');
    }
    
    return issues;
  };

  const validationIssues = validateWorkflow();

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Workflow Settings
      </Typography>
      
      {/* Workflow Validation */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" sx={{ mb: 2, color: 'primary.main' }}>
            🔍 Workflow Validation
          </Typography>
          
          {validationIssues.length === 0 ? (
            <Alert severity="success">
              <Typography variant="body2">
                ✅ Workflow is valid and ready for execution
              </Typography>
            </Alert>
          ) : (
            <Alert severity="warning">
              <Typography variant="body2" sx={{ mb: 1 }}>
                ⚠️ Issues found in workflow:
              </Typography>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {validationIssues.map((issue, index) => (
                  <li key={index}>
                    <Typography variant="body2">{issue}</Typography>
                  </li>
                ))}
              </ul>
            </Alert>
          )}
          
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Chip 
              label={`${actions.length} Actions`} 
              size="small" 
              color="primary" 
              variant="outlined" 
            />
            <Chip 
              label={`${actions.filter(a => a.conditions?.length > 0).length} Conditional`} 
              size="small" 
              color="secondary" 
              variant="outlined" 
            />
            <Chip 
              label={`${actions.filter(a => a.dependencies?.length > 0).length} With Dependencies`} 
              size="small" 
              color="info" 
              variant="outlined" 
            />
          </Box>
        </CardContent>
      </Card>
      
      {/* Execution Settings */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" sx={{ mb: 2, color: 'secondary.main' }}>
            ⚙️ Execution Settings
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.continueOnError}
                    onChange={(e) => setSettings(prev => ({ ...prev, continueOnError: e.target.checked }))}
                  />
                }
                label="Continue workflow on action errors"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.parallelExecution}
                    onChange={(e) => setSettings(prev => ({ ...prev, parallelExecution: e.target.checked }))}
                  />
                }
                label="Enable parallel execution where possible"
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Global Timeout (seconds)"
                value={settings.timeout}
                onChange={(e) => setSettings(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                inputProps={{ min: 30, max: 3600 }}
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Global Retry Count"
                value={settings.retryCount}
                onChange={(e) => setSettings(prev => ({ ...prev, retryCount: parseInt(e.target.value) }))}
                inputProps={{ min: 0, max: 5 }}
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Retry Delay (seconds)"
                value={settings.retryDelay}
                onChange={(e) => setSettings(prev => ({ ...prev, retryDelay: parseInt(e.target.value) }))}
                inputProps={{ min: 1, max: 60 }}
              />
            </Grid>
            
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Execution Mode</InputLabel>
                <Select
                  value={settings.executionMode || 'sequential'}
                  label="Execution Mode"
                  onChange={(e) => setSettings(prev => ({ ...prev, executionMode: e.target.value }))}
                >
                  <MenuItem value="sequential">Sequential (one after another)</MenuItem>
                  <MenuItem value="parallel">Parallel (where possible)</MenuItem>
                  <MenuItem value="batch">Batch (group similar actions)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      
      {/* Logging & Monitoring */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" sx={{ mb: 2, color: 'success.main' }}>
            📊 Logging & Monitoring
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Log Level</InputLabel>
                <Select
                  value={settings.logLevel || 'info'}
                  label="Log Level"
                  onChange={(e) => setSettings(prev => ({ ...prev, logLevel: e.target.value }))}
                >
                  <MenuItem value="debug">Debug (verbose)</MenuItem>
                  <MenuItem value="info">Info (standard)</MenuItem>
                  <MenuItem value="warning">Warning (errors only)</MenuItem>
                  <MenuItem value="error">Error (critical only)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.captureOutput}
                    onChange={(e) => setSettings(prev => ({ ...prev, captureOutput: e.target.checked }))}
                  />
                }
                label="Capture action output for debugging"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableNotifications}
                    onChange={(e) => setSettings(prev => ({ ...prev, enableNotifications: e.target.checked }))}
                  />
                }
                label="Send notifications on workflow completion"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      
      {/* Advanced Options */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">
            🔧 Advanced Options
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Custom Environment Variables (JSON)"
                value={JSON.stringify(settings.environmentVariables || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const env = JSON.parse(e.target.value);
                    setSettings(prev => ({ ...prev, environmentVariables: env }));
                  } catch (err) {
                    // Invalid JSON, don't update
                  }
                }}
                multiline
                rows={4}
                placeholder='{"PATH": "/custom/path", "DEBUG": "true"}'
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Workflow Tags (comma-separated)"
                value={settings.tags?.join(', ') || ''}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  tags: e.target.value.split(',').map(t => t.trim()).filter(t => t) 
                }))}
                placeholder="production, critical, maintenance"
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default ActionsWorkspaceModal;