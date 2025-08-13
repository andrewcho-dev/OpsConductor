/**
 * UI slice for managing global UI state
 */
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  // Sidebar state
  sidebarOpen: true,
  sidebarCollapsed: false,
  
  // Theme
  darkMode: localStorage.getItem('darkMode') === 'true',
  
  // Loading states
  globalLoading: false,
  
  // Notifications/Alerts
  alerts: [],
  
  // Modals
  modals: {
    userCreate: false,
    userEdit: false,
    jobCreate: false,
    jobEdit: false,
    targetCreate: false,
    targetEdit: false,
  },
  
  // Filters and search
  filters: {
    users: {
      role: '',
      status: '',
      search: '',
    },
    jobs: {
      status: '',
      search: '',
      dateRange: null,
    },
    targets: {
      type: '',
      status: '',
      search: '',
    },
  },
  
  // Pagination
  pagination: {
    users: { page: 1, pageSize: 25 },
    jobs: { page: 1, pageSize: 25 },
    targets: { page: 1, pageSize: 25 },
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Sidebar actions
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    
    setSidebarOpen: (state, action) => {
      state.sidebarOpen = action.payload;
    },
    
    toggleSidebarCollapsed: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    
    // Theme actions
    toggleDarkMode: (state) => {
      state.darkMode = !state.darkMode;
      localStorage.setItem('darkMode', state.darkMode.toString());
    },
    
    setDarkMode: (state, action) => {
      state.darkMode = action.payload;
      localStorage.setItem('darkMode', action.payload.toString());
    },
    
    // Loading actions
    setGlobalLoading: (state, action) => {
      state.globalLoading = action.payload;
    },
    
    // Alert actions
    addAlert: (state, action) => {
      const alert = {
        id: Date.now() + Math.random(),
        timestamp: new Date().toISOString(),
        ...action.payload,
      };
      state.alerts.push(alert);
    },
    
    removeAlert: (state, action) => {
      state.alerts = state.alerts.filter(alert => alert.id !== action.payload);
    },
    
    clearAlerts: (state) => {
      state.alerts = [];
    },
    
    // Modal actions
    openModal: (state, action) => {
      const { modalName, data } = action.payload;
      state.modals[modalName] = true;
      if (data) {
        state.modalData = { ...state.modalData, [modalName]: data };
      }
    },
    
    closeModal: (state, action) => {
      const modalName = action.payload;
      state.modals[modalName] = false;
      if (state.modalData && state.modalData[modalName]) {
        delete state.modalData[modalName];
      }
    },
    
    closeAllModals: (state) => {
      Object.keys(state.modals).forEach(key => {
        state.modals[key] = false;
      });
      state.modalData = {};
    },
    
    // Filter actions
    setFilter: (state, action) => {
      const { section, filterName, value } = action.payload;
      if (state.filters[section]) {
        state.filters[section][filterName] = value;
      }
    },
    
    clearFilters: (state, action) => {
      const section = action.payload;
      if (state.filters[section]) {
        Object.keys(state.filters[section]).forEach(key => {
          state.filters[section][key] = '';
        });
      }
    },
    
    // Pagination actions
    setPagination: (state, action) => {
      const { section, page, pageSize } = action.payload;
      if (state.pagination[section]) {
        if (page !== undefined) state.pagination[section].page = page;
        if (pageSize !== undefined) state.pagination[section].pageSize = pageSize;
      }
    },
    
    resetPagination: (state, action) => {
      const section = action.payload;
      if (state.pagination[section]) {
        state.pagination[section].page = 1;
      }
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  toggleSidebarCollapsed,
  toggleDarkMode,
  setDarkMode,
  setGlobalLoading,
  addAlert,
  removeAlert,
  clearAlerts,
  openModal,
  closeModal,
  closeAllModals,
  setFilter,
  clearFilters,
  setPagination,
  resetPagination,
} = uiSlice.actions;

// Selectors
export const selectSidebarOpen = (state) => state.ui.sidebarOpen;
export const selectSidebarCollapsed = (state) => state.ui.sidebarCollapsed;
export const selectDarkMode = (state) => state.ui.darkMode;
export const selectGlobalLoading = (state) => state.ui.globalLoading;
export const selectAlerts = (state) => state.ui.alerts;
export const selectModals = (state) => state.ui.modals;
export const selectModalData = (state) => state.ui.modalData;
export const selectFilters = (state) => state.ui.filters;
export const selectPagination = (state) => state.ui.pagination;

export default uiSlice.reducer;