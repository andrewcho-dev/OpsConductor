/**
 * RTK Query API slice for OpsConductor platform
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const baseQuery = fetchBaseQuery({
  baseUrl: process.env.REACT_APP_API_URL || '',
  prepareHeaders: (headers, { getState }) => {
    // Get token from localStorage since we removed auth Redux state
    const token = localStorage.getItem('access_token');
    
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    
    headers.set('content-type', 'application/json');
    return headers;
  },
});

const baseQueryWithReauth = async (args, api, extraOptions) => {
  let result = await baseQuery(args, api, extraOptions);
  
  if (result.error && result.error.status === 401) {
    // Session expired - redirect to login (no refresh tokens in session-based auth)
    console.log('🚪 Session expired in Redux store, redirecting to login...');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token'); // Remove any old refresh tokens
    window.location.href = '/login';
  }
  
  return result;
};

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['User', 'Job', 'Target', 'Discovery', 'Analytics'],
  endpoints: (builder) => ({
    // Health check endpoint
    healthCheck: builder.query({
      query: () => '/health',
    }),
  }),
});

export const { useHealthCheckQuery } = apiSlice;