# OpsConductor Visual Standards Guide

This guide defines the visual standards for the OpsConductor UI to ensure consistency, space efficiency, and visual continuity across all pages of the application.

## Core Design Principles

1. **Space Efficiency**: Maximize usable screen space with compact components and minimal padding
2. **Data Density**: Prioritize data tables with robust filtering and sorting capabilities
3. **Visual Consistency**: Maintain consistent spacing, typography, and component styling
4. **Functional Clarity**: Ensure UI elements clearly communicate their purpose and state

## Layout Structure

### Page Layout

The application follows a fixed layout structure with three constant elements:

```
┌─────────────────────────────────────────────────────┐
│                    Top Header                       │
├────────┬──────────────────────────────────────────┬─┘
│        │                                          │
│        │                                          │
│        │                                          │
│ Left   │             Content Area                 │
│ Sidebar│                                          │
│        │                                          │
│        │                                          │
│        │                                          │
├────────┴──────────────────────────────────────────┤
│                 Bottom Status Bar                  │
└─────────────────────────────────────────────────────┘
```

- **Top Header**: Fixed height of 64px
- **Left Sidebar**: Fixed width of 240px (expanded) or 60px (collapsed)
- **Content Area**: Flexible, fills available space
- **Bottom Status Bar**: Fixed height of 40px

### Content Area Structure

Each page in the content area should follow this general structure:

```
┌─────────────────────────────────────────────────────┐
│ Page Header                                         │
├─────────────────────────────────────────────────────┤
│ [Optional] Action Bar                               │
├─────────────────────────────────────────────────────┤
│ [Optional] Minimal Stats Cards (max 4 per row)      │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Main Content (primarily data tables)                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Color Palette

The application uses a consistent color palette based on the selected theme. The default theme is Blue.

### Theme Colors

```
Blue (Default):
- Header/Footer: linear-gradient(45deg, #003c82 30%, #0056b3 90%)
- Text on Header/Footer: #ffffff
```

Other available themes include Dark, Green, Purple, Orange, and Red, each with their own gradient definitions.

### Functional Colors

- **Error/Critical**: #f44336 (light: #ffebee)
- **Warning/High**: #ff9800 (light: #fff3e0)
- **Success/Healthy**: #4caf50 (light: #e8f5e9)
- **Info/Normal**: #2196f3 (light: #e3f2fd)
- **Neutral/Background**: #f8f9fa
- **Dividers/Borders**: #e0e0e0

## Typography

### Font Families

- **UI Elements**: System font stack (Roboto or system default)
- **Data/Code**: Monospace font (for tables, code, and technical data)

### Font Sizes

- **Page Titles**: 1.25rem (20px)
- **Section Headers**: 1rem (16px)
- **Regular Text**: 0.875rem (14px)
- **Table Headers**: 0.75rem (12px)
- **Table Data**: 0.75rem (12px)
- **Small/Caption Text**: 0.7rem (11px)
- **Micro Text**: 0.65rem (10px) - Used in status bar

### Font Weights

- **Bold/Headers**: 600
- **Normal Text**: 400
- **Light Text**: 300

## Components

### Data Tables

Data tables are the primary content component and should follow these standards:

#### Table Layout

- **Size**: `size="small"` for all tables
- **Density**: Compact with minimal padding
- **Cell Padding**: 4px 8px (consistent across all cells)
- **Row Height**: Minimize to increase data density
- **Font**: Monospace for all data cells

#### Table Features

- **Column Headers**:
  - Bold, 0.75rem font size
  - Sortable with clear indicators (arrows)
  - Background color: grey.100 (#f5f5f5)

- **Filter Row**:
  - Placed directly below headers
  - Compact filter inputs (2px 4px padding)
  - Background color: grey.50 (#fafafa)

- **Pagination**:
  - Compact (40px height)
  - Options: 5, 10, 25, 50 rows per page

- **Row Styling**:
  - Status-based coloring for critical/error states only
  - Hover effects for better row identification

#### Table Actions

- Small icon buttons with tooltips
- Consistent action placement (right-aligned)
- Standard action icons:
  - View: `<VisibilityIcon />`
  - Edit: `<EditIcon />`
  - Delete: `<DeleteIcon />`
  - Execute: `<PlayArrowIcon />`
  - Stop: `<StopIcon />`

### Cards

Use cards sparingly and only when necessary:

- **Stats Cards**:
  - Height: 100px maximum
  - Width: Equal sizing, 4 per row maximum
  - Padding: 16px
  - Content: Large number/stat with small label

- **Content Cards**:
  - Minimal padding (16px)
  - Clear headers (16px font size)
  - White background
  - Light border or shadow

### Form Elements

- **Text Fields**:
  - Size: `size="small"`
  - Label placement: Top or inline
  - Width: Match content requirements

- **Select Menus**:
  - Size: `size="small"`
  - Compact options (4px 8px padding)
  - Clear placeholder text

- **Buttons**:
  - Size: `size="small"` for most buttons
  - Primary actions: `variant="contained"`
  - Secondary actions: `variant="outlined"`
  - Destructive actions: `color="error"`

### Modals/Dialogs

- **Size**: Appropriate to content, avoid oversized dialogs
- **Title**: Clear, concise (16px font)
- **Content**: Minimal padding (16px)
- **Actions**: Right-aligned, clear primary/secondary distinction

## Spacing

### Margins and Padding

- **Section Spacing**: 16px between major sections
- **Component Spacing**: 8px between related components
- **Internal Padding**: 
  - Cards/Containers: 16px
  - Table Cells: 4px 8px
  - Form Fields: 8px

### Grid System

- Use flexbox or grid for layouts
- Maintain consistent gutters (8px or 16px)
- Prefer equal-width columns when possible

## Icons

- **Size**: `fontSize="small"` (20px) for most UI icons
- **Button Icons**: Consistent sizing within button groups
- **Table Icons**: Smaller (16px) for in-table actions
- **Status Icons**: Use consistent icons for status indicators

## Responsive Behavior

- **Sidebar**: Collapsible to 60px width on smaller screens
- **Tables**: Horizontal scrolling for narrow viewports
- **Cards**: Stack vertically on mobile devices

## Page Templates

### List/Table Page

```
┌─────────────────────────────────────────────────────┐
│ Page Title                           [Action Button] │
├─────────────────────────────────────────────────────┤
│ [Optional] Filter Bar / Bulk Actions                 │
├─────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│ │ Stat 1  │ │ Stat 2  │ │ Stat 3  │ │ Stat 4  │     │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘     │
├─────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────┐   │
│ │ Table Header Row                              │   │
│ ├───────────────────────────────────────────────┤   │
│ │ Filter Row                                    │   │
│ ├───────────────────────────────────────────────┤   │
│ │ Data Row                                      │   │
│ ├───────────────────────────────────────────────┤   │
│ │ Data Row                                      │   │
│ ├───────────────────────────────────────────────┤   │
│ │ ...                                           │   │
│ └───────────────────────────────────────────────┘   │
│ Pagination Controls                                  │
└─────────────────────────────────────────────────────┘
```

### Detail/Form Page

```
┌─────────────────────────────────────────────────────┐
│ Page Title                      [Back] [Save Button] │
├─────────────────────────────────────────────────────┤
│ ┌───────────────────────┐ ┌───────────────────────┐ │
│ │ Section 1             │ │ Section 2             │ │
│ │ ┌───────────────────┐ │ │ ┌───────────────────┐ │ │
│ │ │ Form Field        │ │ │ │ Form Field        │ │ │
│ │ └───────────────────┘ │ │ └───────────────────┘ │ │
│ │ ┌───────────────────┐ │ │ ┌───────────────────┐ │ │
│ │ │ Form Field        │ │ │ │ Form Field        │ │ │
│ │ └───────────────────┘ │ │ └───────────────────┘ │ │
│ └───────────────────────┘ └───────────────────────┘ │
│                                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ Related Data Table                            │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Implementation Guidelines

### CSS Classes and Styling

- Use Material-UI's `sx` prop for component styling
- Follow these patterns for consistent spacing:
  ```jsx
  // Table cell styling
  sx={{
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    padding: '4px 8px'
  }}
  
  // Header styling
  sx={{ 
    fontWeight: 600,
    fontSize: '1.25rem',
    mb: 2
  }}
  
  // Card styling
  sx={{
    p: 2,
    height: '100%',
    display: 'flex',
    flexDirection: 'column'
  }}
  ```

### Component Best Practices

1. **Tables**:
   - Always include filter capabilities
   - Use consistent column widths across related tables
   - Include pagination for all data tables

2. **Forms**:
   - Group related fields
   - Use consistent field widths
   - Provide clear validation feedback

3. **Actions**:
   - Place primary actions in consistent locations
   - Use standard icon buttons for common actions
   - Provide tooltips for all icon-only buttons

## Accessibility Considerations

- Maintain sufficient color contrast (4.5:1 minimum)
- Ensure all interactive elements are keyboard accessible
- Provide text alternatives for all icons (tooltips/aria-labels)
- Maintain logical tab order for form elements

---

By following these visual standards, we ensure that the OpsConductor UI maintains its space-efficient design while providing a consistent and intuitive user experience across all pages.