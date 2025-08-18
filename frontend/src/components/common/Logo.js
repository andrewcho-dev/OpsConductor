import React from 'react';
import { Box } from '@mui/material';
import { useTheme } from '@mui/material/styles';

const Logo = ({ 
  size = 40, 
  sx = {}, 
  alt = "OpsConductor Logo",
  variant = "hat", // "hat", "full", or "legacy"
  theme = "auto", // "auto", "light", "dark"
  ...props 
}) => {
  const muiTheme = useTheme();
  
  // Determine which logo to use based on variant and theme
  const getLogoSrc = () => {
    if (variant === "full") {
      return "/OpsConductor dark on light 640.svg";
    }
    
    if (variant === "legacy") {
      return "/logo.svg";
    }
    
    // Default to hat variant
    if (theme === "dark") {
      return "/OpsConductor hat light on dark.svg";
    } else if (theme === "light") {
      return "/OpsConductor hat dark on light.svg";
    } else {
      // Auto-detect based on MUI theme
      const isDarkMode = muiTheme.palette.mode === 'dark';
      return isDarkMode 
        ? "/OpsConductor hat light on dark.svg"
        : "/OpsConductor hat dark on light.svg";
    }
  };

  return (
    <Box
      component="img"
      src={getLogoSrc()}
      alt={alt}
      sx={{
        height: size,
        width: size,
        objectFit: 'contain',
        ...sx
      }}
      {...props}
    />
  );
};

export default Logo;