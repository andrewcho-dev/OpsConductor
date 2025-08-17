/**
 * Standard Layout Enforcement Utility
 * 
 * This utility provides functions to help migrate pages to the standard layout
 * and validate that pages are following the design system guidelines.
 */

/**
 * Validates if a page component follows the standard layout
 * @param {string} componentPath - Path to the component file
 * @returns {object} Validation results with issues and recommendations
 */
export const validatePageLayout = (componentContent) => {
  const issues = [];
  const recommendations = [];

  // Check for standard container classes
  if (!componentContent.includes('dashboard-container') && !componentContent.includes('datatable-page-container')) {
    issues.push('Missing standard container class (dashboard-container or datatable-page-container)');
    recommendations.push('Wrap your page content in <div className="dashboard-container">');
  }

  // Check for standard header
  if (!componentContent.includes('page-header') && !componentContent.includes('datatable-page-header')) {
    issues.push('Missing standard page header class');
    recommendations.push('Use StandardPageLayout component or add className="page-header" to your header');
  }

  // Check for standard title styling
  if (!componentContent.includes('page-title')) {
    issues.push('Missing standard page title class');
    recommendations.push('Add className="page-title" to your page title Typography component');
  }

  // Check for standard actions area
  if (!componentContent.includes('page-actions')) {
    issues.push('Missing standard page actions area');
    recommendations.push('Wrap action buttons in <div className="page-actions">');
  }

  // Check for non-standard styling patterns
  if (componentContent.includes('sx={{ p: ') || componentContent.includes('sx={{ padding:')) {
    issues.push('Using custom padding instead of standard classes');
    recommendations.push('Remove custom padding and use standard container classes');
  }

  if (componentContent.includes('variant="h4"') || componentContent.includes('variant="h5"')) {
    issues.push('Using non-standard heading variants');
    recommendations.push('Use className="page-title" instead of variant="h4/h5"');
  }

  return {
    isCompliant: issues.length === 0,
    issues,
    recommendations
  };
};

/**
 * Standard layout patterns for different page types
 */
export const layoutPatterns = {
  // Basic page with header and content
  basic: `
import React from 'react';
import StandardPageLayout from '../common/StandardPageLayout';
import { IconButton, Button, Tooltip } from '@mui/material';
import { Refresh as RefreshIcon, Add as AddIcon } from '@mui/icons-material';

const YourPage = () => {
  const actions = (
    <>
      <Tooltip title="Refresh">
        <IconButton className="btn-icon" size="small">
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Button className="btn-compact" variant="contained" size="small">
        Add Item
      </Button>
    </>
  );

  return (
    <StandardPageLayout
      title="Your Page Title"
      actions={actions}
    >
      {/* Your page content here */}
    </StandardPageLayout>
  );
};
`,

  // Page with stats grid
  withStats: `
import React from 'react';
import StandardPageLayout, { StandardStatCard, StandardContentCard } from '../common/StandardPageLayout';
import { IconButton, Tooltip } from '@mui/material';
import { Refresh as RefreshIcon, People as PeopleIcon } from '@mui/icons-material';

const YourPage = () => {
  const actions = (
    <Tooltip title="Refresh">
      <IconButton className="btn-icon" size="small">
        <RefreshIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  );

  const stats = (
    <>
      <StandardStatCard
        icon={<PeopleIcon fontSize="small" />}
        value="123"
        label="Total Items"
        iconColor="primary"
      />
      {/* Add more stat cards as needed */}
    </>
  );

  return (
    <StandardPageLayout
      title="Your Page Title"
      actions={actions}
      stats={stats}
    >
      <StandardContentCard title="MAIN CONTENT" subtitle="Content description">
        {/* Your main content here */}
      </StandardContentCard>
    </StandardPageLayout>
  );
};
`,

  // Data table page
  dataTable: `
import React from 'react';
import StandardPageLayout, { StandardContentCard } from '../common/StandardPageLayout';
import { IconButton, Button, Tooltip } from '@mui/material';
import { Refresh as RefreshIcon, Add as AddIcon } from '@mui/icons-material';

const YourPage = () => {
  const actions = (
    <>
      <Tooltip title="Refresh">
        <IconButton className="btn-icon" size="small">
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Button className="btn-compact" variant="contained" size="small">
        Add Item
      </Button>
    </>
  );

  return (
    <StandardPageLayout
      title="Your Page Title"
      actions={actions}
      containerClass="datatable-page-container"
    >
      <div className="table-content-area">
        {/* Your table component here */}
        {/* Use StandardDataTable or follow table standards */}
      </div>
    </StandardPageLayout>
  );
};
`
};

/**
 * Migration helper - generates the import statements needed for standard layout
 */
export const getStandardImports = () => {
  return `import StandardPageLayout, { StandardContentCard, StandardStatCard } from '../common/StandardPageLayout';
import { IconButton, Button, Tooltip } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';`;
};

/**
 * Common action patterns
 */
export const actionPatterns = {
  refresh: `
    <Tooltip title="Refresh">
      <IconButton className="btn-icon" onClick={handleRefresh} size="small">
        <RefreshIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  `,
  
  add: `
    <Button 
      className="btn-compact" 
      variant="contained" 
      startIcon={<AddIcon fontSize="small" />}
      onClick={handleAdd}
      size="small"
    >
      Add Item
    </Button>
  `,
  
  back: `
    <Tooltip title="Back">
      <IconButton className="btn-icon" onClick={handleBack} size="small">
        <ArrowBackIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  `
};

export default {
  validatePageLayout,
  layoutPatterns,
  getStandardImports,
  actionPatterns
};