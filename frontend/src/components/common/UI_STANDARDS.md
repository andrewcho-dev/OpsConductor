# UI Standardization Guidelines

## Overview
This document outlines the standardized UI components and patterns implemented across the ENABLEDRM system to ensure visual consistency.

## Standardized Components

### 1. Data Table Standards
**Universal standards for all data tables across the system:**

#### Typography
- **Font Family**: `fontFamily: 'monospace'` for ALL text in data tables
- **Consistency**: Every field in every table uses monospace font
- **Example**: Same as timestamp formatting in audit table

#### Status/State Indication
- **❌ NO Colored Badges/Chips**: No `<Chip>` components in table cells
- **✅ Row Background Colors**: Entire row colored based on status/severity
- **Color Mapping**:
  - `error`/`critical`/`failed`: Light red background (`error.light` with `error.contrastText`)
  - `warning`/`medium`/`pending`: Light orange background (`warning.light` with `warning.contrastText`)
  - `success`/`low`/`completed`: Light green background (`success.light` with `success.contrastText`)
  - `info`/`running`: Light blue background (`info.light` with `info.contrastText`)
  - Default: No background color
- **✅ Hover Inversion**: On hover, colors invert (background becomes text color, text becomes background color)

#### Layout & Spacing
- **Zero Padding**: `padding: '0px'` for all table cells (absolute maximum density)
- **First Column Exception**: `padding: '0px 0px 0px 4px'` for first column (prevents text touching left edge)
- **Ultra-Dense Layout**: No whitespace padding - pure data display
- **Footer Clearance**: `marginBottom: '80px'` on main containers to prevent overlap with footer

#### Actions
- **❌ NO Text Buttons**: No `<Button>` components in table cells
- **✅ Icon Actions Only**: Use standardized action components
- **Standard Icons**: ViewDetailsAction, EditAction, DeleteAction, etc.
- **Compact Icons**: `fontSize="small"` and `padding: '2px'` for minimal row height impact

#### Refresh Functionality
- **❌ NO "Refresh" Text Buttons**: Anywhere in the system
- **✅ RefreshAction Icon Only**: Use `<RefreshIcon>` with tooltip

### 2. Search Cards (`SearchCard.js`)
- **Purpose**: Compact, consistent search interface
- **Features**:
  - No section labels (removed "Search Audit Events", etc.)
  - Compact height with `py: 2` padding
  - Small form controls (`size="small"`)
  - Outlined card variant
  - Flexible filter and action configuration

**Usage Example**:
```jsx
<SearchCard
  searchValue={searchQuery}
  onSearchChange={setSearchQuery}
  searchPlaceholder="Search items..."
  filters={[...]}
  actions={[...]}
/>
```

### 2. Standard Actions (`StandardActions.js`)
Consistent icon-based actions replacing text buttons:

#### Refresh Actions
- **Component**: `RefreshAction`
- **Icon**: `RefreshIcon`
- **Usage**: Replace all "Refresh" text buttons
- **Tooltip**: "Refresh"

#### View Details Actions
- **Component**: `ViewDetailsAction`
- **Icon**: `VisibilityIcon` (eyeball)
- **Usage**: Replace all "View" text buttons
- **Tooltip**: "View Details"

#### Edit Actions
- **Component**: `EditAction`
- **Icon**: `EditIcon`
- **Usage**: Replace all "Edit" text buttons
- **Tooltip**: "Edit"

#### Delete Actions
- **Component**: `DeleteAction`
- **Icon**: `DeleteIcon`
- **Usage**: Replace all "Delete" text buttons
- **Tooltip**: "Delete"
- **Color**: `error`

#### Close Actions (Modals)
- **Component**: `CloseAction`
- **Icon**: `CloseIcon`
- **Position**: Absolute positioned in upper right corner
- **Usage**: Replace DialogActions close buttons
- **Style**: Standard "X" in top-right corner

#### Other Actions
- `PlayAction`, `StopAction`, `PauseAction`, `AddAction`, `DownloadAction`, `UploadAction`, `SettingsAction`

## Implementation Status

### ✅ Completed Components
1. **AuditDashboard**
   - ✅ Removed redundant overview tab - direct to search interface
   - ✅ **COLUMN-BASED FILTERING**: Individual filters above each column
   - ✅ ViewDetailsAction for event details
   - ✅ CloseAction in modal header
   - ✅ RefreshAction in page header
   - ✅ **TABLE STANDARDS**: Monospace font, row coloring by severity, no chips

2. **UserList**
   - ✅ RefreshAction in toolbar
   - ✅ EditAction and DeleteAction in table rows
   - ✅ **COLUMN-BASED FILTERING**: Individual filters above each column
   - ✅ **TABLE STANDARDS**: Monospace font, row coloring by status, no chips

3. **UniversalTargetList**
   - ✅ ViewDetailsAction, EditAction, DeleteAction in table rows
   - ✅ **COLUMN-BASED FILTERING**: Individual filters above each column
   - ✅ **TABLE STANDARDS**: Monospace font, row coloring by health, no chips

4. **JobList**
   - ✅ ViewDetailsAction, EditAction, DeleteAction, StopAction in table rows
   - ✅ **COLUMN-BASED FILTERING**: Individual filters above each column
   - ✅ **TABLE STANDARDS**: Monospace font, row coloring by status, no chips

5. **CommunicationMethodsManager**
   - ✅ CloseAction in modal header
   - ✅ Removed DialogActions close button

### 🔄 Standardization Rules Applied

#### Search & Filtering Interfaces
- ❌ **Before**: Large cards with "Search [Items]" labels
- ✅ **After**: Column-based filtering directly above table columns
- **Column Filters**: Individual filter inputs positioned above each column
- **Monospace Styling**: Filter inputs match table column formatting
- **Real-time Filtering**: Instant client-side filtering as user types
- **Smart Controls**: Text inputs for searchable fields, dropdowns for enums

#### Action Buttons
- ❌ **Before**: Text buttons like "View", "Edit", "Delete", "Refresh"
- ✅ **After**: Icon buttons with tooltips using standard components

#### Modal Close Buttons
- ❌ **Before**: "Close" button in DialogActions
- ✅ **After**: "X" icon in upper right corner of DialogTitle

#### Refresh Actions
- ❌ **Before**: Various refresh button implementations
- ✅ **After**: Consistent `RefreshAction` component

## Visual Benefits

1. **Consistency**: Same icons and styling across all components
2. **Space Efficiency**: Compact search cards and icon actions save space
3. **Professional Appearance**: Clean, modern interface with standard patterns
4. **User Experience**: Familiar patterns (X to close, eyeball to view, etc.)
5. **Maintainability**: Centralized action components for easy updates

## Usage Guidelines

### For New Components
1. Use `SearchCard` for all search interfaces
2. Use standard action components instead of custom buttons
3. Use `CloseAction` for modal close functionality
4. Follow the established sizing patterns (`size="small"`)

### For Existing Components
1. Replace text-based action buttons with icon actions
2. Update search interfaces to use `SearchCard`
3. Remove unnecessary section labels
4. Standardize modal close patterns

## File Locations
- **SearchCard**: `/src/components/common/SearchCard.js`
- **StandardActions**: `/src/components/common/StandardActions.js`
- **Documentation**: `/src/components/common/UI_STANDARDS.md`