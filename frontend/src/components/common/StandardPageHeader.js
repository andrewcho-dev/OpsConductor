/**
 * Standard Page Header Component
 * Provides 100% consistent styling across all pages
 */
import React from 'react';
import { Typography, Box } from '@mui/material';
import '../../styles/dashboard.css';

const StandardPageHeader = ({ 
    title, 
    children, 
    className = '',
    ...props 
}) => {
    return (
        <div className={`page-header ${className}`} {...props}>
            <Typography className="page-title">
                {title}
            </Typography>
            <div className="page-actions">
                {children}
            </div>
        </div>
    );
};

export default StandardPageHeader;