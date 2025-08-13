import React from 'react';
import { Box } from '@mui/material';

const Logo = ({ 
  size = 40, 
  sx = {}, 
  alt = "OpsConductor Logo",
  ...props 
}) => {
  return (
    <Box
      component="img"
      src="/logo.svg"
      alt={alt}
      sx={{
        height: size,
        width: size,
        ...sx
      }}
      {...props}
    />
  );
};

export default Logo;