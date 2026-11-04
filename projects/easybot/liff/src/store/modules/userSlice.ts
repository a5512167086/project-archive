import { createSlice } from "@reduxjs/toolkit";
import { userApi, UserOrdersResponse } from "../apis/userApi";
import { UserReservationsResponse } from "../apis/userApi";

interface UserState {
  userReservations: UserReservationsResponse;
  userOrders: UserOrdersResponse;
  errorCode: string;
  errorMessage: string;
  status: "idle" | "loading" | "succeeded" | "failed";
}

const initialState: UserState = {
  userReservations: [],
  userOrders: [],
  errorCode: "",
  errorMessage: "",
  status: "idle",
};

export const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    clearUserError: (state) => {
      state.errorCode = "";
      state.errorMessage = "";
      state.status = "idle";
    },
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        userApi.endpoints.getUserReservations.matchPending,
        (state) => {
          state.status = "loading";
        }
      )
      .addMatcher(
        userApi.endpoints.getUserReservations.matchFulfilled,
        (state, action) => {
          state.status = "succeeded";
          state.userReservations = action.payload;
        }
      )
      .addMatcher(userApi.endpoints.getUserOrders.matchPending, (state) => {
        state.status = "loading";
      })
      .addMatcher(
        userApi.endpoints.getUserOrders.matchFulfilled,
        (state, action) => {
          state.status = "succeeded";
          state.userOrders = action.payload;
        }
      );
  },
});

export const { clearUserError } = userSlice.actions;

export default userSlice.reducer;
