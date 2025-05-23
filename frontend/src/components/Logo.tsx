import React from 'react';
import { Box } from '@mui/material';

interface LogoProps {
  size?: number;
  withShadow?: boolean;
}

/**
 * Heart-shaped logo component that displays the EDUGuard logo
 */
const Logo: React.FC<LogoProps> = ({ size = 40, withShadow = true }) => {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: '50%',
        bgcolor: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: withShadow ? '0 4px 8px rgba(0,0,0,0.1)' : 'none',
      }}
    >
      <Box
        sx={{
          width: size * 0.65,
          height: size * 0.65,
          borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
          bgcolor: '#4caf50',
          position: 'relative',
          transform: 'rotate(45deg)',
          '&:before, &:after': {
            content: '""',
            position: 'absolute',
            width: '100%',
            height: '100%',
            borderRadius: '50%',
            bgcolor: '#4caf50',
          },
          '&:before': {
            left: -size * 0.325,
            top: 0,
          },
          '&:after': {
            top: -size * 0.325,
            left: 0,
          }
        }}
      />
    </Box>
  );
};

export default Logo; 