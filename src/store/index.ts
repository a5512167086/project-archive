import { configureStore } from "@reduxjs/toolkit";
import { useDispatch, useSelector } from "react-redux";
import type { TypedUseSelectorHook } from "react-redux";
import { baseApi } from "./apis/baseApi";
import ecommReducer from "./modules/ecommSlice";
import reservationReducer from "./modules/reservationSlice";
import userReducer from "./modules/userSlice";
import cartReducer from "./modules/cartSlice";
import botReducer from "./modules/botSlice";
import moduleReducer from "./modules/moduleSlice";

export const store = configureStore({
  reducer: {
    ecomm: ecommReducer,
    reservation: reservationReducer,
    user: userReducer,
    cart: cartReducer,
    bot: botReducer,
    module: moduleReducer,
    [baseApi.reducerPath]: baseApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(baseApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// 使用 typed hooks
export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
