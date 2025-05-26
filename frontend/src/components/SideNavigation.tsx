import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Divider,
  Avatar,
  Typography,
  IconButton,
  Tooltip,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PersonIcon from '@mui/icons-material/Person';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import AssessmentIcon from '@mui/icons-material/Assessment';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import { useAuth } from '../contexts/AuthContext';
import Logo from '../assets/logo.png';

const drawerExpandedWidth = 280;
const drawerCollapsedWidth = 72;

interface SideNavigationProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

const SideNavigation: React.FC<SideNavigationProps> = ({
  mobileOpen = false,
  onMobileClose = () => {},
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  // Default to expanded state on desktop, collapsed only on tablets
  const [isCollapsed, setIsCollapsed] = useState<boolean>(isTablet);
  
  // Update isCollapsed state when screen size changes
  useEffect(() => {
    setIsCollapsed(isTablet);
  }, [isTablet]);

  const handleNavigation = (path: string) => {
    navigate(path);
    onMobileClose();
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Reports', icon: <AssessmentIcon />, path: '/reports' },
    { text: 'Profile', icon: <PersonIcon />, path: '/profile' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  const drawer = (
    <>
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100%',
        overflow: 'hidden'
      }}>
        <Toolbar sx={{ 
          display: 'flex', 
          justifyContent: isCollapsed ? 'center' : 'space-between',
          alignItems: 'center', 
          py: 2.5,
          px: isCollapsed ? 1 : 2
        }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: isCollapsed ? 'center' : 'flex-start',
            width: '100%'
          }}>
            {/* Logo */}
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <img 
                src={Logo} 
                alt="Logo" 
                style={{ 
                  width: isMobile ? 32 : isCollapsed ? 36 : 42, 
                  height: 'auto',
                  objectFit: 'contain'
                }} 
              />
              {!isCollapsed && (
                <Typography variant="h6" noWrap sx={{ fontWeight: 'bold', ml: 2.5 }}>
                  EDUGuard
                </Typography>
              )}
            </Box>
          </Box>
          
          {/* Collapse toggle button - hide on mobile */}
          <IconButton 
            onClick={toggleCollapse}
            sx={{ 
              display: { xs: 'none', sm: 'flex' },
              ml: isCollapsed ? 0 : 1,
              color: 'primary.main'
            }}
          >
            {isCollapsed ? <MenuIcon /> : <ChevronLeftIcon />}
          </IconButton>
        </Toolbar>
        
        {/* User info - only show when not collapsed */}
        {!isCollapsed && user && (
          <Box sx={{ px: 2, py: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <Avatar sx={{ bgcolor: 'secondary.main', width: 40, height: 40, mr: 2 }}>
                {user.email ? user.email[0].toUpperCase() : 'U'}
              </Avatar>
              <Box sx={{ overflow: 'hidden' }}>
                <Typography variant="body1" sx={{ fontWeight: 'medium', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                  {user.email?.split('@')[0]}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Student
                </Typography>
              </Box>
            </Box>
          </Box>
        )}
        
        <Divider sx={{ display: isCollapsed || !user ? 'block' : 'none' }} />
        
        {/* Menu items */}
        <List sx={{ mt: 1.5, flex: 1, overflowY: 'auto', px: isCollapsed ? 0 : 0 }}>
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <ListItem key={item.text} disablePadding sx={{ mb: 1, width: '100%' }}>
                <Tooltip title={isCollapsed ? item.text : ""} placement="right">
                  <ListItemButton 
                    selected={isActive} 
                    onClick={() => handleNavigation(item.path)}
                    sx={{ 
                      borderRadius: isCollapsed ? 1.5 : 0, 
                      mr: isCollapsed ? 0 : 0,
                      ml: isCollapsed ? 0 : 0,
                      px: isCollapsed ? 1.5 : 2.5,
                      py: 1.5,
                      width: '100%',
                      justifyContent: isCollapsed ? 'center' : 'flex-start',
                      '&.Mui-selected': {
                        backgroundColor: 'primary.light',
                        '&:hover': {
                          backgroundColor: 'primary.light',
                        }
                      }
                    }}
                  >
                    <ListItemIcon 
                      sx={{ 
                        color: isActive ? 'primary.dark' : 'inherit',
                        minWidth: isCollapsed ? 'auto' : 40,
                        mr: isCollapsed ? 0 : 1.5,
                        fontSize: '1.2rem'
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    {!isCollapsed && (
                      <ListItemText 
                        primary={item.text} 
                        primaryTypographyProps={{ 
                          fontWeight: isActive ? 600 : 400,
                          noWrap: true,
                          fontSize: '0.95rem'
                        }} 
                      />
                    )}
                  </ListItemButton>
                </Tooltip>
              </ListItem>
            );
          })}
        </List>
        
        <Divider />
        
        {/* Logout button */}
        <List sx={{ mt: 'auto', mb: 1, px: isCollapsed ? 0 : 0 }}>
          <ListItem disablePadding sx={{ mt: 0.5, width: '100%' }}>
            <Tooltip title={isCollapsed ? "Logout" : ""} placement="right">
              <ListItemButton 
                onClick={handleLogout} 
                sx={{ 
                  borderRadius: isCollapsed ? 1.5 : 0, 
                  mr: isCollapsed ? 0 : 0,
                  ml: isCollapsed ? 0 : 0,
                  px: isCollapsed ? 1.5 : 2.5,
                  py: 1.5,
                  width: '100%',
                  justifyContent: isCollapsed ? 'center' : 'flex-start'
                }}
              >
                <ListItemIcon sx={{ 
                  minWidth: isCollapsed ? 'auto' : 40,
                  mr: isCollapsed ? 0 : 1.5,
                  fontSize: '1.2rem'
                }}>
                  <LogoutIcon color="error" />
                </ListItemIcon>
                {!isCollapsed && (
                  <ListItemText 
                    primary="Logout" 
                    primaryTypographyProps={{ 
                      color: 'error.main',
                      fontSize: '0.95rem'
                    }} 
                  />
                )}
              </ListItemButton>
            </Tooltip>
          </ListItem>
        </List>
      </Box>
    </>
  );

  return (
    <>
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{
          keepMounted: true, // Better mobile performance
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { 
            width: drawerExpandedWidth, 
            boxSizing: 'border-box' 
          },
        }}
      >
        {drawer}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': { 
            width: isCollapsed ? drawerCollapsedWidth : drawerExpandedWidth, 
            boxSizing: 'border-box',
            borderRight: '1px solid rgba(0, 0, 0, 0.08)',
            boxShadow: 'none',
            transition: theme => theme.transitions.create(['width'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.standard,
            }),
            overflowX: 'hidden',
            position: 'fixed',
            zIndex: theme.zIndex.drawer,
            height: '100%',
            left: 0,
            top: 0,
            backgroundColor: theme.palette.background.paper,
          },
          width: isCollapsed ? drawerCollapsedWidth : drawerExpandedWidth,
          flexShrink: 0,
          transition: theme => theme.transitions.create(['width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.standard,
          }),
        }}
        open
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default SideNavigation; 