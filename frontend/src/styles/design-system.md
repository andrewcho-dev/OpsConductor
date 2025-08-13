# EnableDRM Design System
## Compact, Modern, Efficient Control Dashboard Style

### Design Principles
1. **Maximize Space Efficiency** - No wasted white space, compact layouts
2. **Information Density** - More data visible at once without clutter
3. **Consistent Patterns** - Standardized components across all pages
4. **Modern Aesthetics** - Clean, professional, control panel feel
5. **Responsive Design** - Works on all screen sizes

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ Top Header (64px)                                       │
├─────────────────────────────────────────────────────────┤
│ Page Content Area                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Page Header (compact, 48px)                         │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ Stats Grid (compact cards, 80px height)             │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ Main Content Card                                   │ │
│ │ ├─ Card Header (40px)                               │ │
│ │ ├─ Filters/Search (48px)                            │ │
│ │ ├─ Data Table (compact rows, 36px each)             │ │
│ │ └─ Pagination (40px)                                │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Bottom Status Bar (28px) + Alert Panel (expandable)    │
└─────────────────────────────────────────────────────────┘
```

### Typography Scale
- **Page Title**: 20px, weight 600
- **Card Headers**: 12px, weight 600, uppercase
- **Body Text**: 12px, weight 400
- **Captions**: 10px, weight 400
- **Table Headers**: 10px, weight 600, uppercase

### Color Palette
- **Primary**: #1976d2 (blue)
- **Success**: #4caf50 (green)
- **Warning**: #ff9800 (orange)
- **Error**: #f44336 (red)
- **Info**: #2196f3 (light blue)
- **Background**: #f8f9fa (light gray)
- **Cards**: #ffffff (white)
- **Borders**: #e0e0e0 (light gray)

### Component Standards

#### Buttons
- **Height**: 32px
- **Font Size**: 11px
- **Padding**: 0 12px
- **Border Radius**: 4px
- **Icon Size**: 16px

#### Form Controls
- **Height**: 32px
- **Font Size**: 12px
- **Border Radius**: 4px

#### Cards
- **Border**: 1px solid #e0e0e0
- **Border Radius**: 6px
- **Shadow**: 0 1px 2px rgba(0,0,0,0.05)
- **Padding**: 12px

#### Tables
- **Row Height**: 36px
- **Font Size**: 12px
- **Header**: 10px, uppercase, weight 600
- **Cell Padding**: 8px 12px

#### Chips
- **Height**: 20px
- **Font Size**: 10px
- **Border Radius**: 4px

### Spacing System
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **xxl**: 24px

### Page Template Structure
Every function page should follow this structure:

1. **Page Header** (48px height)
   - Page title (left)
   - Action buttons (right)

2. **Stats Grid** (optional, 80px height)
   - 4-8 compact stat cards
   - Icons + numbers + labels

3. **Main Content Card**
   - Card header with section title
   - Filters/search bar
   - Data table or content
   - Pagination if needed

4. **Modals/Dialogs**
   - Consistent styling
   - Compact form layouts

### Implementation Classes
Use these CSS classes for consistency:

- `.dashboard-container` - Main page wrapper
- `.page-header` - Page title section
- `.stats-grid` - Statistics cards container
- `.stat-card` - Individual stat card
- `.main-content-card` - Main content wrapper
- `.filters-container` - Search/filter controls
- `.compact-table` - Data tables
- `.btn-compact` - Standard buttons
- `.form-control-compact` - Form inputs
- `.chip-compact` - Status chips

### Alert System
- Alerts appear in bottom status bar
- Expandable panel shows alert history
- Auto-dismiss for success/info (3-5 seconds)
- Manual dismiss for errors/warnings
- Color-coded by severity