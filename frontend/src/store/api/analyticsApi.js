/**
 * Analytics API endpoints using RTK Query
 */
import { apiSlice } from './apiSlice';

export const analyticsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get dashboard metrics
    getDashboardMetrics: builder.query({
      query: () => '/api/v1/analytics/dashboard',
      providesTags: ['Analytics'],
      transformResponse: (response) => response.data || response,
    }),

    // Get job performance analysis
    getJobPerformanceAnalysis: builder.query({
      query: (jobId = null) => ({
        url: '/api/v1/analytics/jobs/performance',
        params: jobId ? { job_id: jobId } : {},
      }),
      providesTags: ['JobPerformance'],
      transformResponse: (response) => response.data || response,
    }),

    // Get system health report
    getSystemHealthReport: builder.query({
      query: () => '/api/v1/analytics/system/health',
      providesTags: ['SystemHealth'],
      transformResponse: (response) => response.data || response,
    }),

    // Get execution trends
    getExecutionTrends: builder.query({
      query: (days = 30) => ({
        url: '/api/v1/analytics/trends/executions',
        params: { days },
      }),
      providesTags: ['ExecutionTrends'],
      transformResponse: (response) => response.data || response,
    }),

    // Get summary report
    getSummaryReport: builder.query({
      query: () => '/api/v1/analytics/reports/summary',
      providesTags: ['SummaryReport'],
      transformResponse: (response) => response.data || response,
    }),
  }),
});

export const {
  useGetDashboardMetricsQuery,
  useGetJobPerformanceAnalysisQuery,
  useGetSystemHealthReportQuery,
  useGetExecutionTrendsQuery,
  useGetSummaryReportQuery,
} = analyticsApi;