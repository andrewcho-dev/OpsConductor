/**
 * RTK Query API slice for OpsConductor platform
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const baseQuery = fetchBaseQuery({
  baseUrl: process.env.REACT_APP_API_URL || '',
  prepareHeaders: (headers, { getState }) => {
    // Get token from auth state
    const token = getState().auth.token || localStorage.getItem('access_token');
    
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
    // Try to refresh token
    const refreshResult = await baseQuery(
      {
        url: '/api/v3/auth/refresh',
        method: 'POST',
        body: {
          refresh_token: localStorage.getItem('refresh_token'),
        },
      },
      api,
      extraOptions
    );
    
    if (refreshResult.data) {
      // Store new token
      const { access_token, refresh_token } = refreshResult.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Update auth state (import authSlice actions separately)
      // api.dispatch(authSlice.actions.setCredentials({
      //   token: access_token,
      //   refreshToken: refresh_token,
      // }));
      
      // Retry original query
      result = await baseQuery(args, api, extraOptions);
    } else {
      // Refresh failed, logout user
      // api.dispatch(authSlice.actions.logout());
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
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