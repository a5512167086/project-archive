import { configureStore } from '@reduxjs/toolkit'
import userReducer from './modules/userSlice'
import botReducer from './modules/botSlice'
import moduleReducer from './modules/moduleSlice'
import knowledgeReducer from './modules/knowledgeSlice'
import { userApi } from './apis/userApi'
import { botApi } from './apis/botApi'
import { moduleApi } from './apis/moduleApi'
import { knowledgeApi } from './apis/knowledgeApi'

export const store = configureStore({
  reducer: {
    user: userReducer,
    bot: botReducer,
    module: moduleReducer,
    knowledge: knowledgeReducer,
    [userApi.reducerPath]: userApi.reducer,
    [botApi.reducerPath]: botApi.reducer,
    [moduleApi.reducerPath]: moduleApi.reducer,
    [knowledgeApi.reducerPath]: knowledgeApi.reducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(userApi.middleware)
      .concat(botApi.middleware)
      .concat(moduleApi.middleware)
      .concat(knowledgeApi.middleware)
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
