#!/usr/bin/env node

/**
 * Layout Standards Validation Script
 * 
 * This script validates that all page components follow the standard layout guidelines.
 * Run with: node validate-layout-standards.js
 */

const fs = require('fs');
const path = require('path');

// Page components to validate
const pageComponents = [
  'src/components/dashboard/Dashboard.js',

  'src/components/targets/UniversalTargetDashboard.js',
  'src/components/jobs/JobDashboard.js',
  'src/components/system/SystemHealthDashboard.js',
  'src/components/system/SystemSettings.jsx',
  'src/components/audit/AuditDashboard.js'
];

/**
 * Validates if a page component follows the standard layout
 */
function validatePageLayout(componentContent, filePath) {
  const issues = [];
  const recommendations = [];
  const fileName = path.basename(filePath);

  // Check for standard container classes
  if (!componentContent.includes('dashboard-container') && 
      !componentContent.includes('datatable-page-container') &&
      !componentContent.includes('StandardPageLayout')) {
    issues.push('Missing standard container class or StandardPageLayout component');
    recommendations.push('Use StandardPageLayout component or add className="dashboard-container"');
  }

  // Check for standard header
  if (!componentContent.includes('page-header') && 
      !componentContent.includes('datatable-page-header') &&
      !componentContent.includes('StandardPageLayout')) {
    issues.push('Missing standard page header');
    recommendations.push('Use StandardPageLayout component or add className="page-header"');
  }

  // Check for standard title styling
  if (!componentContent.includes('page-title') && !componentContent.includes('StandardPageLayout')) {
    issues.push('Missing standard page title class');
    recommendations.push('Add className="page-title" to your page title');
  }

  // Check for standard actions area
  if (!componentContent.includes('page-actions') && !componentContent.includes('StandardPageLayout')) {
    issues.push('Missing standard page actions area');
    recommendations.push('Wrap action buttons in <div className="page-actions">');
  }

  // Check for non-standard styling patterns (exclude input field padding)
  const hasContainerPadding = componentContent.includes('sx={{ p: 3') || 
                              componentContent.includes('sx={{ padding: 3') ||
                              componentContent.includes('sx={{ p: 2') ||
                              componentContent.includes('sx={{ padding: 2');
  if (hasContainerPadding && !componentContent.includes('StandardPageLayout')) {
    issues.push('Using custom container padding instead of standard classes');
    recommendations.push('Remove custom container padding and use StandardPageLayout or standard container classes');
  }

  if (componentContent.includes('variant="h4"') || componentContent.includes('variant="h5"')) {
    issues.push('Using non-standard heading variants');
    recommendations.push('Use className="page-title" instead of variant="h4/h5"');
  }

  // Check for proper button classes
  if (componentContent.includes('<Button') && !componentContent.includes('btn-compact')) {
    issues.push('Buttons may not be using standard btn-compact class');
    recommendations.push('Add className="btn-compact" to Button components');
  }

  if (componentContent.includes('<IconButton') && !componentContent.includes('btn-icon')) {
    issues.push('Icon buttons may not be using standard btn-icon class');
    recommendations.push('Add className="btn-icon" to IconButton components');
  }

  // Check for proper icon sizing
  if (componentContent.includes('<RefreshIcon') && !componentContent.includes('fontSize="small"')) {
    issues.push('Icons may not be using standard fontSize="small"');
    recommendations.push('Add fontSize="small" to all icon components');
  }

  return {
    fileName,
    isCompliant: issues.length === 0,
    issues,
    recommendations
  };
}

/**
 * Main validation function
 */
function validateAllPages() {
  console.log('🔍 Validating Layout Standards Compliance...\n');
  
  let totalPages = 0;
  let compliantPages = 0;
  const results = [];

  pageComponents.forEach(componentPath => {
    const fullPath = path.join(__dirname, componentPath);
    
    if (!fs.existsSync(fullPath)) {
      console.log(`⚠️  File not found: ${componentPath}`);
      return;
    }

    try {
      const componentContent = fs.readFileSync(fullPath, 'utf8');
      const validation = validatePageLayout(componentContent, componentPath);
      
      totalPages++;
      if (validation.isCompliant) {
        compliantPages++;
      }
      
      results.push(validation);
    } catch (error) {
      console.log(`❌ Error reading ${componentPath}: ${error.message}`);
    }
  });

  // Display results
  console.log('📊 VALIDATION RESULTS\n');
  console.log(`Total Pages: ${totalPages}`);
  console.log(`Compliant Pages: ${compliantPages}`);
  console.log(`Non-Compliant Pages: ${totalPages - compliantPages}`);
  console.log(`Compliance Rate: ${Math.round((compliantPages / totalPages) * 100)}%\n`);

  // Show detailed results
  results.forEach(result => {
    if (result.isCompliant) {
      console.log(`✅ ${result.fileName} - COMPLIANT`);
    } else {
      console.log(`❌ ${result.fileName} - NON-COMPLIANT`);
      result.issues.forEach(issue => {
        console.log(`   • Issue: ${issue}`);
      });
      result.recommendations.forEach(rec => {
        console.log(`   • Fix: ${rec}`);
      });
      console.log('');
    }
  });

  // Summary
  if (compliantPages === totalPages) {
    console.log('\n🎉 ALL PAGES ARE COMPLIANT WITH LAYOUT STANDARDS!');
    console.log('✨ Your application has 100% consistent layout formatting.');
  } else {
    console.log(`\n⚠️  ${totalPages - compliantPages} pages need attention to achieve full compliance.`);
    console.log('📖 See recommendations above for specific fixes needed.');
  }

  return {
    totalPages,
    compliantPages,
    complianceRate: Math.round((compliantPages / totalPages) * 100)
  };
}

// Run validation if this script is executed directly
if (require.main === module) {
  validateAllPages();
}

module.exports = { validatePageLayout, validateAllPages };