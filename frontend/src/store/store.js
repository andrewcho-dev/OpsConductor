/**
 * Redux store configuration with RTK Query
 */
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query/react';

// Import slices

import uiSlice from './slices/uiSlice';
import jobsSlice from './slices/jobsSlice';
import targetsSlice from './slices/targetsSlice';

// Import API slices
import { apiSlice } from './api/apiSlice';
import { usersApi } from './api/usersApi';

export const store = configureStore({
  reducer: {
    // API slices
    [apiSlice.reducerPath]: apiSlice.reducer,
    [usersApi.reducerPath]: usersApi.reducer,
    
    // Feature slices
    ui: uiSlice,
    jobs: jobsSlice,
    targets: targetsSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(apiSlice.middleware, usersApi.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

// Enable listener behavior for the store
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;