/**
 * Jobs slice for job-related state management
 */
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  // Job lists
  jobs: [],
  executions: [],
  
  // Selected items
  selectedJob: null,
  selectedExecution: null,
  
  // Loading states
  loading: {
    jobs: false,
    executions: false,
    creating: false,
    updating: false,
    executing: false,
  },
  
  // Error states
  errors: {
    jobs: null,
    executions: null,
    create: null,
    update: null,
    execute: null,
  },
  
  // Real-time execution monitoring
  activeExecutions: {},
  executionLogs: {},
  
  // Job statistics
  stats: {
    total: 0,
    running: 0,
    completed: 0,
    failed: 0,
    scheduled: 0,
  },
  
  // Filters and sorting
  filters: {
    status: '',
    type: '',
    dateRange: null,
    search: '',
  },
  
  sorting: {
    field: 'created_at',
    direction: 'desc',
  },
};

const jobsSlice = createSlice({
  name: 'jobs',
  initialState,
  reducers: {
    // Job list actions
    setJobs: (state, action) => {
      state.jobs = action.payload;
      state.loading.jobs = false;
      state.errors.jobs = null;
    },
    
    addJob: (state, action) => {
      state.jobs.unshift(action.payload);
    },
    
    updateJob: (state, action) => {
      const index = state.jobs.findIndex(job => job.id === action.payload.id);
      if (index !== -1) {
        state.jobs[index] = { ...state.jobs[index], ...action.payload };
      }
    },
    
    removeJob: (state, action) => {
      state.jobs = state.jobs.filter(job => job.id !== action.payload);
    },
    
    // Execution actions
    setExecutions: (state, action) => {
      state.executions = action.payload;
      state.loading.executions = false;
      state.errors.executions = null;
    },
    
    addExecution: (state, action) => {
      state.executions.unshift(action.payload);
    },
    
    updateExecution: (state, action) => {
      const index = state.executions.findIndex(exec => exec.id === action.payload.id);
      if (index !== -1) {
        state.executions[index] = { ...state.executions[index], ...action.payload };
      }
      
      // Update active executions if it's currently running
      if (state.activeExecutions[action.payload.id]) {
        state.activeExecutions[action.payload.id] = {
          ...state.activeExecutions[action.payload.id],
          ...action.payload,
        };
      }
    },
    
    // Selection actions
    setSelectedJob: (state, action) => {
      state.selectedJob = action.payload;
    },
    
    setSelectedExecution: (state, action) => {
      state.selectedExecution = action.payload;
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
    
    // Real-time execution monitoring
    startExecutionMonitoring: (state, action) => {
      const execution = action.payload;
      state.activeExecutions[execution.id] = execution;
    },
    
    stopExecutionMonitoring: (state, action) => {
      const executionId = action.payload;
      delete state.activeExecutions[executionId];
    },
    
    updateExecutionProgress: (state, action) => {
      const { executionId, progress } = action.payload;
      if (state.activeExecutions[executionId]) {
        state.activeExecutions[executionId].progress = progress;
      }
    },
    
    addExecutionLog: (state, action) => {
      const { executionId, log } = action.payload;
      if (!state.executionLogs[executionId]) {
        state.executionLogs[executionId] = [];
      }
      state.executionLogs[executionId].push(log);
    },
    
    clearExecutionLogs: (state, action) => {
      const executionId = action.payload;
      delete state.executionLogs[executionId];
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
        status: '',
        type: '',
        dateRange: null,
        search: '',
      };
    },
    
    setSorting: (state, action) => {
      const { field, direction } = action.payload;
      state.sorting.field = field;
      state.sorting.direction = direction;
    },
    
    // Reset actions
    resetJobsState: (state) => {
      return { ...initialState, filters: state.filters, sorting: state.sorting };
    },
  },
});

export const {
  setJobs,
  addJob,
  updateJob,
  removeJob,
  setExecutions,
  addExecution,
  updateExecution,
  setSelectedJob,
  setSelectedExecution,
  setLoading,
  setError,
  clearError,
  startExecutionMonitoring,
  stopExecutionMonitoring,
  updateExecutionProgress,
  addExecutionLog,
  clearExecutionLogs,
  setStats,
  setFilter,
  clearFilters,
  setSorting,
  resetJobsState,
} = jobsSlice.actions;

// Selectors
export const selectJobs = (state) => state.jobs.jobs;
export const selectExecutions = (state) => state.jobs.executions;
export const selectSelectedJob = (state) => state.jobs.selectedJob;
export const selectSelectedExecution = (state) => state.jobs.selectedExecution;
export const selectJobsLoading = (state) => state.jobs.loading;
export const selectJobsErrors = (state) => state.jobs.errors;
export const selectActiveExecutions = (state) => state.jobs.activeExecutions;
export const selectExecutionLogs = (state) => state.jobs.executionLogs;
export const selectJobsStats = (state) => state.jobs.stats;
export const selectJobsFilters = (state) => state.jobs.filters;
export const selectJobsSorting = (state) => state.jobs.sorting;

export default jobsSlice.reducer;