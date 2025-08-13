/**
 * Targets slice for target management state
 */
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  // Target lists
  targets: [],
  discoveredDevices: [],
  
  // Selected items
  selectedTarget: null,
  selectedTargets: [],
  
  // Loading states
  loading: {
    targets: false,
    discovery: false,
    creating: false,
    updating: false,
    testing: false,
  },
  
  // Error states
  errors: {
    targets: null,
    discovery: null,
    create: null,
    update: null,
    test: null,
  },
  
  // Connection test results
  connectionTests: {},
  
  // Target statistics
  stats: {
    total: 0,
    online: 0,
    offline: 0,
    unknown: 0,
    byType: {},
  },
  
  // Discovery state
  discovery: {
    isRunning: false,
    progress: 0,
    currentRange: null,
    results: [],
  },
  
  // Filters and sorting
  filters: {
    type: '',
    status: '',
    search: '',
    tags: [],
  },
  
  sorting: {
    field: 'name',
    direction: 'asc',
  },
  
  // Bulk operations
  bulkOperations: {
    selectedIds: [],
    operation: null,
    progress: 0,
  },
};

const targetsSlice = createSlice({
  name: 'targets',
  initialState,
  reducers: {
    // Target list actions
    setTargets: (state, action) => {
      state.targets = action.payload;
      state.loading.targets = false;
      state.errors.targets = null;
    },
    
    addTarget: (state, action) => {
      state.targets.unshift(action.payload);
    },
    
    updateTarget: (state, action) => {
      const index = state.targets.findIndex(target => target.id === action.payload.id);
      if (index !== -1) {
        state.targets[index] = { ...state.targets[index], ...action.payload };
      }
    },
    
    removeTarget: (state, action) => {
      state.targets = state.targets.filter(target => target.id !== action.payload);
      state.selectedTargets = state.selectedTargets.filter(id => id !== action.payload);
    },
    
    // Selection actions
    setSelectedTarget: (state, action) => {
      state.selectedTarget = action.payload;
    },
    
    setSelectedTargets: (state, action) => {
      state.selectedTargets = action.payload;
    },
    
    toggleTargetSelection: (state, action) => {
      const targetId = action.payload;
      const index = state.selectedTargets.indexOf(targetId);
      if (index === -1) {
        state.selectedTargets.push(targetId);
      } else {
        state.selectedTargets.splice(index, 1);
      }
    },
    
    selectAllTargets: (state) => {
      state.selectedTargets = state.targets.map(target => target.id);
    },
    
    clearTargetSelection: (state) => {
      state.selectedTargets = [];
    },
    
    // Discovery actions
    setDiscoveredDevices: (state, action) => {
      state.discoveredDevices = action.payload;
      state.loading.discovery = false;
      state.errors.discovery = null;
    },
    
    addDiscoveredDevice: (state, action) => {
      state.discoveredDevices.push(action.payload);
    },
    
    updateDiscoveredDevice: (state, action) => {
      const index = state.discoveredDevices.findIndex(device => device.id === action.payload.id);
      if (index !== -1) {
        state.discoveredDevices[index] = { ...state.discoveredDevices[index], ...action.payload };
      }
    },
    
    removeDiscoveredDevice: (state, action) => {
      state.discoveredDevices = state.discoveredDevices.filter(device => device.id !== action.payload);
    },
    
    // Discovery process actions
    startDiscovery: (state, action) => {
      state.discovery.isRunning = true;
      state.discovery.progress = 0;
      state.discovery.currentRange = action.payload.range;
      state.discovery.results = [];
    },
    
    updateDiscoveryProgress: (state, action) => {
      state.discovery.progress = action.payload;
    },
    
    addDiscoveryResult: (state, action) => {
      state.discovery.results.push(action.payload);
    },
    
    stopDiscovery: (state) => {
      state.discovery.isRunning = false;
      state.discovery.progress = 100;
    },
    
    resetDiscovery: (state) => {
      state.discovery = {
        isRunning: false,
        progress: 0,
        currentRange: null,
        results: [],
      };
    },
    
    // Connection test actions
    setConnectionTest: (state, action) => {
      const { targetId, result } = action.payload;
      state.connectionTests[targetId] = result;
    },
    
    clearConnectionTest: (state, action) => {
      const targetId = action.payload;
      delete state.connectionTests[targetId];
    },
    
    // Loading actions
    setLoading: (state, action) => {
      const { type, value } = action.payload;
      state.loading[type] = value;
    },
    
    // Error actions
    setError: (state, action) => {
      const { type, error } = action.payload;
      state.errors[type] = error;
      if (state.loading[type] !== undefined) {
        state.loading[type] = false;
      }
    },
    
    clearError: (state, action) => {
      const type = action.payload;
      state.errors[type] = null;
    },
    
    // Statistics actions
    setStats: (state, action) => {
      state.stats = { ...state.stats, ...action.payload };
    },
    
    // Filter and sorting actions
    setFilter: (state, action) => {
      const { filterName, value } = action.payload;
      state.filters[filterName] = value;
    },
    
    clearFilters: (state) => {
      state.filters = {
        type: '',
        status: '',
        search: '',
        tags: [],
      };
    },
    
    setSorting: (state, action) => {
      const { field, direction } = action.payload;
      state.sorting.field = field;
      state.sorting.direction = direction;
    },
    
    // Bulk operations
    setBulkOperation: (state, action) => {
      const { operation, selectedIds } = action.payload;
      state.bulkOperations.operation = operation;
      state.bulkOperations.selectedIds = selectedIds || state.selectedTargets;
      state.bulkOperations.progress = 0;
    },
    
    updateBulkProgress: (state, action) => {
      state.bulkOperations.progress = action.payload;
    },
    
    clearBulkOperation: (state) => {
      state.bulkOperations = {
        selectedIds: [],
        operation: null,
        progress: 0,
      };
    },
    
    // Reset actions
    resetTargetsState: (state) => {
      return { ...initialState, filters: state.filters, sorting: state.sorting };
    },
  },
});

export const {
  setTargets,
  addTarget,
  updateTarget,
  removeTarget,
  setSelectedTarget,
  setSelectedTargets,
  toggleTargetSelection,
  selectAllTargets,
  clearTargetSelection,
  setDiscoveredDevices,
  addDiscoveredDevice,
  updateDiscoveredDevice,
  removeDiscoveredDevice,
  startDiscovery,
  updateDiscoveryProgress,
  addDiscoveryResult,
  stopDiscovery,
  resetDiscovery,
  setConnectionTest,
  clearConnectionTest,
  setLoading,
  setError,
  clearError,
  setStats,
  setFilter,
  clearFilters,
  setSorting,
  setBulkOperation,
  updateBulkProgress,
  clearBulkOperation,
  resetTargetsState,
} = targetsSlice.actions;

// Selectors
export const selectTargets = (state) => state.targets.targets;
export const selectDiscoveredDevices = (state) => state.targets.discoveredDevices;
export const selectSelectedTarget = (state) => state.targets.selectedTarget;
export const selectSelectedTargets = (state) => state.targets.selectedTargets;
export const selectTargetsLoading = (state) => state.targets.loading;
export const selectTargetsErrors = (state) => state.targets.errors;
export const selectConnectionTests = (state) => state.targets.connectionTests;
export const selectTargetsStats = (state) => state.targets.stats;
export const selectDiscoveryState = (state) => state.targets.discovery;
export const selectTargetsFilters = (state) => state.targets.filters;
export const selectTargetsSorting = (state) => state.targets.sorting;
export const selectBulkOperations = (state) => state.targets.bulkOperations;

export default targetsSlice.reducer;