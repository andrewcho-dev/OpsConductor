/**
 * Targets API endpoints using RTK Query
 */
import { apiSlice } from './apiSlice';

export const targetsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get targets with pagination and filtering
    getTargets: builder.query({
      query: ({ 
        page = 1, 
        pageSize = 25, 
        search = '', 
        targetType = '', 
        status = '',
        tags = []
      } = {}) => ({
        url: '/targets/',
        params: {
          skip: (page - 1) * pageSize,
          limit: pageSize,
          ...(search && { search }),
          ...(targetType && { target_type: targetType }),
          ...(status && { status }),
          ...(tags.length > 0 && { tags: tags.join(',') }),
        },
      }),
      providesTags: ['Target'],
      transformResponse: (response) => response.data || response,
    }),

    // Get target by ID
    getTargetById: builder.query({
      query: (id) => `/targets/${id}`,
      providesTags: (result, error, id) => [{ type: 'Target', id }],
      transformResponse: (response) => response.data || response,
    }),

    // Create new target
    createTarget: builder.mutation({
      query: (targetData) => ({
        url: '/targets/',
        method: 'POST',
        body: targetData,
      }),
      invalidatesTags: ['Target'],
      transformResponse: (response) => response.data || response,
    }),

    // Update target
    updateTarget: builder.mutation({
      query: ({ id, ...targetData }) => ({
        url: `/targets/${id}`,
        method: 'PUT',
        body: targetData,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Target', id },
        'Target',
      ],
      transformResponse: (response) => response.data || response,
    }),

    // Delete target
    deleteTarget: builder.mutation({
      query: (id) => ({
        url: `/targets/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Target'],
    }),

    // Test target connection
    testTargetConnection: builder.mutation({
      query: (id) => ({
        url: `/targets/${id}/test`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [{ type: 'Target', id }],
    }),

    // Bulk test connections
    bulkTestConnections: builder.mutation({
      query: (targetIds) => ({
        url: '/targets/bulk/test',
        method: 'POST',
        body: targetIds,
      }),
      invalidatesTags: ['Target'],
    }),

    // Bulk update targets
    bulkUpdateTargets: builder.mutation({
      query: ({ targetIds, updateData }) => ({
        url: '/targets/bulk/update',
        method: 'POST',
        body: {
          target_ids: targetIds,
          update_data: updateData,
        },
      }),
      invalidatesTags: ['Target'],
    }),

    // Get target statistics
    getTargetStatistics: builder.query({
      query: () => '/targets/statistics/overview',
      providesTags: ['TargetStats'],
      transformResponse: (response) => response.data || response,
    }),

    // Get targets needing health check
    getTargetsNeedingHealthCheck: builder.query({
      query: (minutesSinceLastCheck = 30) => ({
        url: '/targets/health/check',
        params: { minutes_since_last_check: minutesSinceLastCheck },
      }),
      providesTags: ['TargetHealth'],
      transformResponse: (response) => response.data || response,
    }),

    // Perform health checks
    performHealthChecks: builder.mutation({
      query: () => ({
        url: '/targets/health/perform',
        method: 'POST',
      }),
      invalidatesTags: ['Target', 'TargetHealth'],
    }),

    // Get target types
    getTargetTypes: builder.query({
      query: () => '/targets/types',
      transformResponse: (response) => response.target_types || [],
    }),
  }),
});

export const {
  useGetTargetsQuery,
  useGetTargetByIdQuery,
  useCreateTargetMutation,
  useUpdateTargetMutation,
  useDeleteTargetMutation,
  useTestTargetConnectionMutation,
  useBulkTestConnectionsMutation,
  useBulkUpdateTargetsMutation,
  useGetTargetStatisticsQuery,
  useGetTargetsNeedingHealthCheckQuery,
  usePerformHealthChecksMutation,
  useGetTargetTypesQuery,
} = targetsApi;