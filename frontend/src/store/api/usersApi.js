/**
 * Users API endpoints using RTK Query
 */
import { apiSlice } from './apiSlice';

export const usersApi = apiSlice.injectEndpoints({
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

    // Change password
    changePassword: builder.mutation({
      query: ({ id, currentPassword, newPassword }) => ({
        url: `/users/${id}/change-password`,
        method: 'POST',
        body: {
          current_password: currentPassword,
          new_password: newPassword,
        },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'User', id }],
    }),

    // Deactivate user
    deactivateUser: builder.mutation({
      query: (id) => ({
        url: `/users/${id}/deactivate`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'User', id },
        'User',
      ],
      transformResponse: (response) => response.data || response,
    }),

    // Activate user
    activateUser: builder.mutation({
      query: (id) => ({
        url: `/users/${id}/activate`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'User', id },
        'User',
      ],
      transformResponse: (response) => response.data || response,
    }),

    // Delete user (if implemented)
    deleteUser: builder.mutation({
      query: (id) => ({
        url: `/users/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['User'],
    }),
  }),
});

export const {
  useGetUsersQuery,
  useGetUserByIdQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useChangePasswordMutation,
  useDeactivateUserMutation,
  useActivateUserMutation,
  useDeleteUserMutation,
} = usersApi;