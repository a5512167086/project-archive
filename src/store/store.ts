import { configureStore } from '@reduxjs/toolkit'
import userReducer from './modules/userSlice'
import botReducer from './modules/botSlice'
import searchReducer from './modules/searchSlice'
import { userApi } from './apis/userApi'
import { botApi } from './apis/botApi'
import { searchApi } from './apis/searchApi'

export const store = configureStore({
  reducer: {
    user: userReducer,
    bot: botReducer,
    search: searchReducer,
    [userApi.reducerPath]: userApi.reducer,
    [botApi.reducerPath]: botApi.reducer,
    [searchApi.reducerPath]: searchApi.reducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(userApi.middleware)
      .concat(botApi.middleware)
      .concat(searchApi.middleware)
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
