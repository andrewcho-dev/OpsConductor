/**
 * Standardized Action Components
 * Provides consistent icons and styling for common actions across the system
 */
import React from 'react';
import {
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
  Add as AddIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon
} from '@mui/icons-material';

// Standard Refresh Action
export const RefreshAction = ({ onClick, disabled = false, size = "medium", ...props }) => (
  <Tooltip title="Refresh">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      {...props}
    >
      <RefreshIcon />
    </IconButton>
  </Tooltip>
);

// Standard View Details Action
export const ViewDetailsAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="View Details">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      sx={{ padding: '2px', ...props.sx }}
      {...props}
    >
      <VisibilityIcon fontSize="small" />
    </IconButton>
  </Tooltip>
);

// Standard Edit Action
export const EditAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="Edit">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      sx={{ padding: '2px', ...props.sx }}
      {...props}
    >
      <EditIcon fontSize="small" />
    </IconButton>
  </Tooltip>
);

// Standard Delete Action
export const DeleteAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="Delete">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      color="error"
      sx={{ padding: '2px', ...props.sx }}
      {...props}
    >
      <DeleteIcon fontSize="small" />
    </IconButton>
  </Tooltip>
);

// Standard Close Action (for modals)
export const CloseAction = ({ onClick, disabled = false, size = "small", sx = {}, ...props }) => (
  <IconButton 
    onClick={onClick} 
    disabled={disabled}
    size={size}
    sx={{
      position: 'absolute',
      right: 8,
      top: 8,
      color: (theme) => theme.palette.grey[500],
      ...sx
    }}
    {...props}
  >
    <CloseIcon />
  </IconButton>
);

// Standard Add Action
export const AddAction = ({ onClick, disabled = false, size = "medium", ...props }) => (
  <Tooltip title="Add">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      color="primary"
      {...props}
    >
      <AddIcon />
    </IconButton>
  </Tooltip>
);

// Standard Download Action
export const DownloadAction = ({ onClick, disabled = false, size = "small", title = "Download", ...props }) => (
  <Tooltip title={title}>
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      {...props}
    >
      <DownloadIcon />
    </IconButton>
  </Tooltip>
);

// Standard Upload Action
export const UploadAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="Upload">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      {...props}
    >
      <UploadIcon />
    </IconButton>
  </Tooltip>
);

// Standard Settings Action
export const SettingsAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="Settings">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      {...props}
    >
      <SettingsIcon />
    </IconButton>
  </Tooltip>
);

// Standard Play Action
export const PlayAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="Run">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      color="success"
      sx={{ padding: '2px', ...props.sx }}
      {...props}
    >
      <PlayIcon fontSize="small" />
    </IconButton>
  </Tooltip>
);

// Standard Stop Action
export const StopAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="Stop">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      color="error"
      sx={{ padding: '2px', ...props.sx }}
      {...props}
    >
      <StopIcon fontSize="small" />
    </IconButton>
  </Tooltip>
);

// Standard Pause Action
export const PauseAction = ({ onClick, disabled = false, size = "small", ...props }) => (
  <Tooltip title="Pause">
    <IconButton 
      onClick={onClick} 
      disabled={disabled}
      size={size}
      color="warning"
      {...props}
    >
      <PauseIcon />
    </IconButton>
  </Tooltip>
);