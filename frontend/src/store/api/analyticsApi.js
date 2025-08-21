/**
 * Analytics API endpoints using RTK Query
 */
import { apiSlice } from './apiSlice';

export const analyticsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get dashboard metrics
    getDashboardMetrics: builder.query({
      query: () => '/analytics/dashboard',
      providesTags: ['Analytics'],
      transformResponse: (response) => response.data || response,
    }),

    // Get job performance analysis
    getJobPerformanceAnalysis: builder.query({
      query: (jobId = null) => ({
        url: '/analytics/jobs/performance',
        params: jobId ? { job_id: jobId } : {},
      }),
      providesTags: ['JobPerformance'],
      transformResponse: (response) => response.data || response,
    }),



    // Get execution trends
    getExecutionTrends: builder.query({
      query: (days = 30) => ({
        url: '/analytics/trends/executions',
        params: { days },
      }),
      providesTags: ['ExecutionTrends'],
      transformResponse: (response) => response.data || response,
    }),

    // Get summary report
    getSummaryReport: builder.query({
      query: () => '/analytics/reports/summary',
      providesTags: ['SummaryReport'],
      transformResponse: (response) => response.data || response,
    }),
  }),
});

export const {
  useGetDashboardMetricsQuery,
  useGetJobPerformanceAnalysisQuery,
  useGetExecutionTrendsQuery,
  useGetSummaryReportQuery,
} = analyticsApi;