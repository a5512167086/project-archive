import { configureStore } from '@reduxjs/toolkit'
import userReducer from './modules/userSlice'
import botReducer from './modules/botSlice'
import moduleReducer from './modules/moduleSlice'
import knowledgeReducer from './modules/knowledgeSlice'
import reservationReducer from './modules/reservationSlice'
import brandReducer from './modules/brandSlice'
import categoryReducer from './modules/categorySlice'
import productReducer from './modules/productSlice'
import ecommReducer from './modules/ecommSlice'
import orderReducer from './modules/orderSlice'
import { baseApi } from './apis/baseApi'

export const store = configureStore({
  reducer: {
    user: userReducer,
    bot: botReducer,
    module: moduleReducer,
    knowledge: knowledgeReducer,
    reservation: reservationReducer,
    brand: brandReducer,
    category: categoryReducer,
    product: productReducer,
    ecomm: ecommReducer,
    order: orderReducer,
    [baseApi.reducerPath]: baseApi.reducer
  },

  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(baseApi.middleware)
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
