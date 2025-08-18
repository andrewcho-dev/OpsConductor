/**
 * Jobs API endpoints using RTK Query - SIMPLIFIED v3
 */
import { apiSlice } from './apiSlice';

export const jobsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get jobs with pagination and filtering
    getJobs: builder.query({
      query: ({ 
        skip = 0, 
        limit = 100
      } = {}) => ({
        url: '/api/v3/jobs/',
        params: {
          skip,
          limit
        },
      }),
      providesTags: ['Job'],
    }),

    // Get job by ID
    getJobById: builder.query({
      query: (id) => `/api/v3/jobs/${id}`,
      providesTags: (result, error, id) => [{ type: 'Job', id }],
    }),

    // Get job executions
    getJobExecutions: builder.query({
      query: (jobId) => `/api/v3/jobs/${jobId}/executions`,
      providesTags: (result, error, jobId) => [{ type: 'JobExecution', jobId }],
    }),

    // Get execution results
    getExecutionResults: builder.query({
      query: ({ jobId, executionNumber, targetId }) => ({
        url: `/api/v3/jobs/${jobId}/executions/${executionNumber}/results`,
        params: targetId ? { target_id: targetId } : {}
      }),
      providesTags: (result, error, { jobId, executionNumber }) => [
        { type: 'ExecutionResult', jobId, executionNumber }
      ],
    }),

    // Get target results
    getTargetResults: builder.query({
      query: ({ targetId, limit = 100 }) => ({
        url: `/api/v3/jobs/targets/${targetId}/results`,
        params: { limit }
      }),
      providesTags: (result, error, { targetId }) => [
        { type: 'TargetResult', targetId }
      ],
    }),

    // Create job
    createJob: builder.mutation({
      query: (jobData) => ({
        url: '/api/v3/jobs/',
        method: 'POST',
        body: jobData,
      }),
      invalidatesTags: ['Job'],
    }),

    // Execute job
    executeJob: builder.mutation({
      query: ({ id, target_ids }) => ({
        url: `/api/v3/jobs/${id}/execute`,
        method: 'POST',
        body: { target_ids },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Job', id },
        { type: 'JobExecution', jobId: id }
      ],
    }),

    // Delete job
    deleteJob: builder.mutation({
      query: (id) => ({
        url: `/api/v3/jobs/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Job'],
    }),
  }),
});

export const {
  useGetJobsQuery,
  useGetJobByIdQuery,
  useGetJobExecutionsQuery,
  useGetExecutionResultsQuery,
  useGetTargetResultsQuery,
  useCreateJobMutation,
  useExecuteJobMutation,
  useDeleteJobMutation,
} = jobsApi;