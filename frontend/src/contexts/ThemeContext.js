import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Default theme presets
export const THEME_PRESETS = {
  blue: {
    name: 'Blue (Default)',
    headerBackground: 'linear-gradient(45deg, #003c82 30%, #0056b3 90%)',
    headerColor: '#ffffff',
    bottomBarBackground: 'linear-gradient(45deg, #003c82 30%, #0056b3 90%)',
    bottomBarColor: '#ffffff',
  },
  dark: {
    name: 'Dark',
    headerBackground: 'linear-gradient(45deg, #2c3e50 30%, #34495e 90%)',
    headerColor: '#ffffff',
    bottomBarBackground: 'linear-gradient(45deg, #2c3e50 30%, #34495e 90%)',
    bottomBarColor: '#ffffff',
  },
  green: {
    name: 'Green',
    headerBackground: 'linear-gradient(45deg, #27ae60 30%, #2ecc71 90%)',
    headerColor: '#ffffff',
    bottomBarBackground: 'linear-gradient(45deg, #27ae60 30%, #2ecc71 90%)',
    bottomBarColor: '#ffffff',
  },
  purple: {
    name: 'Purple',
    headerBackground: 'linear-gradient(45deg, #8e44ad 30%, #9b59b6 90%)',
    headerColor: '#ffffff',
    bottomBarBackground: 'linear-gradient(45deg, #8e44ad 30%, #9b59b6 90%)',
    bottomBarColor: '#ffffff',
  },
  orange: {
    name: 'Orange',
    headerBackground: 'linear-gradient(45deg, #e67e22 30%, #f39c12 90%)',
    headerColor: '#ffffff',
    bottomBarBackground: 'linear-gradient(45deg, #e67e22 30%, #f39c12 90%)',
    bottomBarColor: '#ffffff',
  },
  red: {
    name: 'Red',
    headerBackground: 'linear-gradient(45deg, #c0392b 30%, #e74c3c 90%)',
    headerColor: '#ffffff',
    bottomBarBackground: 'linear-gradient(45deg, #c0392b 30%, #e74c3c 90%)',
    bottomBarColor: '#ffffff',
  },
};

export const ThemeProvider = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState('blue');

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('opsconductor-theme');
    if (savedTheme && THEME_PRESETS[savedTheme]) {
      setCurrentTheme(savedTheme);
    }
  }, []);

  // Save theme to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('opsconductor-theme', currentTheme);
  }, [currentTheme]);

  const changeTheme = (themeKey) => {
    if (THEME_PRESETS[themeKey]) {
      setCurrentTheme(themeKey);
    }
  };

  const getTheme = () => {
    return THEME_PRESETS[currentTheme];
  };

  const value = {
    currentTheme,
    changeTheme,
    getTheme,
    availableThemes: THEME_PRESETS,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};