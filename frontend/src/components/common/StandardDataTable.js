/**
 * Standard Data Table Component
 * Provides 100% consistent table styling and pagination across all pages
 */
import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Typography,
  Select,
  MenuItem,
  Pagination
} from '@mui/material';
import '../../styles/dashboard.css';

const StandardDataTable = ({
  // Table content
  children,
  
  // Pagination props
  currentPage = 1,
  pageSize = 25,
  totalItems = 0,
  onPageChange,
  onPageSizeChange,
  
  // Page size options
  pageSizeOptions = [25, 50, 100, 200],
  
  // Labels
  itemLabel = 'items',
  
  // Container props
  className = '',
  ...props
}) => {
  const totalPages = Math.ceil(totalItems / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  return (
    <div className={`table-content-area ${className}`} {...props}>
      {/* Table Container */}
      <TableContainer 
        component={Paper} 
        variant="outlined"
        className="standard-table-container"
      >
        <Table size="small">
          {children}
        </Table>
      </TableContainer>
      
      {/* Pagination Controls */}
      <div className="standard-pagination-area">
        {/* Page Size Selector */}
        <div className="standard-page-size-selector">
          <Typography variant="body2" className="standard-pagination-info">
            Show:
          </Typography>
          <Select
            value={pageSize}
            onChange={(e) => onPageSizeChange && onPageSizeChange(Number(e.target.value))}
            size="small"
            className="standard-page-size-selector"
          >
            {pageSizeOptions.map(size => (
              <MenuItem key={size} value={size}>{size}</MenuItem>
            ))}
          </Select>
          <Typography variant="body2" className="standard-pagination-info">
            per page
          </Typography>
        </div>

        {/* Pagination */}
        {totalItems > pageSize && (
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(event, page) => onPageChange && onPageChange(page)}
            color="primary"
            size="small"
            variant="outlined"
            className="standard-pagination"
          />
        )}
        
        {/* Pagination Info */}
        <Typography variant="body2" className="standard-pagination-info">
          Showing {startIndex + 1}-{endIndex} of {totalItems} {itemLabel}
        </Typography>
      </div>
    </div>
  );
};

// Standard Table Header Cell
export const StandardTableHeader = ({ children, className = '', ...props }) => (
  <TableCell className={`standard-table-header ${className}`} {...props}>
    {children}
  </TableCell>
);

// Standard Table Data Cell
export const StandardTableCell = ({ children, className = '', ...props }) => (
  <TableCell className={`standard-table-cell ${className}`} {...props}>
    {children}
  </TableCell>
);

// Standard Filter Cell
export const StandardFilterCell = ({ children, className = '', ...props }) => (
  <TableCell className={`standard-filter-cell ${className}`} {...props}>
    {children}
  </TableCell>
);

export default StandardDataTable;