/**
 * Users API endpoints using RTK Query
 * Uses auth service endpoints - NO HARDCODED URLS
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const authBaseQuery = fetchBaseQuery({
  baseUrl: process.env.REACT_APP_AUTH_URL || '/api/auth',
  prepareHeaders: (headers, { getState }) => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    
    headers.set('content-type', 'application/json');
    return headers;
  },
});

const authBaseQueryWithReauth = async (args, api, extraOptions) => {
  let result = await authBaseQuery(args, api, extraOptions);
  
  if (result.error && result.error.status === 401) {
    console.log('🚪 Auth service session expired, redirecting to login...');
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }
  
  return result;
};

export const usersApi = createApi({
  reducerPath: 'usersApi',
  baseQuery: authBaseQueryWithReauth,
  tagTypes: ['User'],
  endpoints: (builder) => ({
    // Get users with pagination and filtering
    getUsers: builder.query({
      query: ({ page = 1, pageSize = 25, role = '', status = '', search = '' } = {}) => ({
        url: '/users/',
        params: {
          skip: (page - 1) * pageSize,
          limit: pageSize,
          ...(role && { role }),
          ...(status && { active_only: status === 'active' }),
          ...(search && { search }),
        },
      }),
      providesTags: ['User'],
      transformResponse: (response) => response.data || response,
    }),

    // Get user by ID
    getUserById: builder.query({
      query: (id) => `/users/${id}`,
      providesTags: (result, error, id) => [{ type: 'User', id }],
      transformResponse: (response) => response.data || response,
    }),

    // Create new user
    createUser: builder.mutation({
      query: (userData) => ({
        url: '/users/',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
      transformResponse: (response) => response.data || response,
    }),

    // Update user
    updateUser: builder.mutation({
      query: ({ id, ...userData }) => ({
        url: `/users/${id}`,
        method: 'PUT',
        body: userData,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        'User',
      ],
      transformResponse: (response) => response.data || response,
    }),

    // Delete user
    deleteUser: builder.mutation({
      query: (id) => ({
        url: `/users/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['User'],
    }),

    // Change own password
    changePassword: builder.mutation({
      query: ({ currentPassword, newPassword }) => ({
        url: '/users/change-password',
        method: 'POST',
        body: {
          current_password: currentPassword,
          new_password: newPassword,
        },
      }),
    }),

    // Admin reset user password
    resetUserPassword: builder.mutation({
      query: ({ id, newPassword }) => ({
        url: `/users/${id}/reset-password`,
        method: 'POST',
        body: {
          new_password: newPassword,
        },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'User', id }],
    }),

    // Toggle user status (activate/deactivate)
    toggleUserStatus: builder.mutation({
      query: (id) => ({
        url: `/users/${id}/toggle-status`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'User', id },
        'User',
      ],
      transformResponse: (response) => response.data || response,
    }),
  }),
});

// Export hooks for usage in functional components
export const {
  useGetUsersQuery,
  useGetUserByIdQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
  useChangePasswordMutation,
  useResetUserPasswordMutation,
  useToggleUserStatusMutation,
} = usersApi;