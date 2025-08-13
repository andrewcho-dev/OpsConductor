/**
 * Jobs API endpoints using RTK Query
 */
import { apiSlice } from './apiSlice';

export const jobsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get jobs with pagination and filtering
    getJobs: builder.query({
      query: ({ 
        page = 1, 
        pageSize = 25, 
        status = '', 
        type = '', 
        search = '',
        dateRange = null 
      } = {}) => ({
        url: '/api/jobs/',
        params: {
          skip: (page - 1) * pageSize,
          limit: pageSize,
          ...(status && { status }),
          ...(type && { job_type: type }),
          ...(search && { search }),
          ...(dateRange && { 
            start_date: dateRange.start,
            end_date: dateRange.end 
          }),
        },
      }),
      providesTags: ['Job'],
      transformResponse: (response) => response.data || response,
    }),

    // Get job by ID
    getJobById: builder.query({
      query: (id) => `/api/jobs/${id}`,
      providesTags: (result, error, id) => [{ type: 'Job', id }],
      transformResponse: (response) => response.data || response,
    }),

    // Get job executions
    getJobExecutions: builder.query({
      query: ({ 
        jobId = null, 
        page = 1, 
        pageSize = 25, 
        status = '' 
      } = {}) => ({
        url: '/api/jobs/executions/',
        params: {
          skip: (page - 1) * pageSize,
          limit: pageSize,
          ...(jobId && { job_id: jobId }),
          ...(status && { status }),
        },
      }),
      providesTags: ['JobExecution'],
      transformResponse: (response) => response.data || response,
    }),

    // Get job execution by ID
    getJobExecutionById: builder.query({
      query: (id) => `/api/jobs/executions/${id}`,
      providesTags: (result, error, id) => [{ type: 'JobExecution', id }],
      transformResponse: (response) => response.data || response,
    }),

    // Create new job
    createJob: builder.mutation({
      query: (jobData) => ({
        url: '/api/jobs/',
        method: 'POST',
        body: jobData,
      }),
      invalidatesTags: ['Job'],
      transformResponse: (response) => response.data || response,
    }),

    // Update job
    updateJob: builder.mutation({
      query: ({ id, ...jobData }) => ({
        url: `/api/jobs/${id}`,
        method: 'PUT',
        body: jobData,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Job', id },
        'Job',
      ],
      transformResponse: (response) => response.data || response,
    }),

    // Execute job
    executeJob: builder.mutation({
      query: ({ id, params = {} }) => ({
        url: `/api/jobs/${id}/execute`,
        method: 'POST',
        body: { execution_params: params },
      }),
      invalidatesTags: ['JobExecution'],
      transformResponse: (response) => response.data || response,
    }),

    // Delete job
    deleteJob: builder.mutation({
      query: (id) => ({
        url: `/api/jobs/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Job'],
    }),

    // Get job statistics
    getJobStatistics: builder.query({
      query: () => '/api/jobs/statistics',
      providesTags: ['JobStats'],
      transformResponse: (response) => response.data || response,
    }),

    // Get running executions
    getRunningExecutions: builder.query({
      query: () => '/api/jobs/executions/running',
      providesTags: ['JobExecution'],
      transformResponse: (response) => response.data || response,
    }),

    // Stop job execution
    stopJobExecution: builder.mutation({
      query: (executionId) => ({
        url: `/api/jobs/executions/${executionId}/stop`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, executionId) => [
        { type: 'JobExecution', id: executionId },
        'JobExecution',
      ],
    }),

    // Get job execution logs
    getJobExecutionLogs: builder.query({
      query: ({ executionId, page = 1, pageSize = 100 }) => ({
        url: `/api/jobs/executions/${executionId}/logs`,
        params: {
          skip: (page - 1) * pageSize,
          limit: pageSize,
        },
      }),
      providesTags: (result, error, { executionId }) => [
        { type: 'JobExecutionLogs', id: executionId }
      ],
      transformResponse: (response) => response.data || response,
    }),

    // Schedule job
    scheduleJob: builder.mutation({
      query: ({ id, scheduleConfig }) => ({
        url: `/api/jobs/${id}/schedule`,
        method: 'POST',
        body: { schedule_config: scheduleConfig },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Job', id },
        'Job',
      ],
    }),

    // Unschedule job
    unscheduleJob: builder.mutation({
      query: (id) => ({
        url: `/api/jobs/${id}/unschedule`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Job', id },
        'Job',
      ],
    }),
  }),
});

export const {
  useGetJobsQuery,
  useGetJobByIdQuery,
  useGetJobExecutionsQuery,
  useGetJobExecutionByIdQuery,
  useCreateJobMutation,
  useUpdateJobMutation,
  useExecuteJobMutation,
  useDeleteJobMutation,
  useGetJobStatisticsQuery,
  useGetRunningExecutionsQuery,
  useStopJobExecutionMutation,
  useGetJobExecutionLogsQuery,
  useScheduleJobMutation,
  useUnscheduleJobMutation,
} = jobsApi;