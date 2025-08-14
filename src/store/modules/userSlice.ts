import { createSlice } from "@reduxjs/toolkit";
import { userApi } from "../apis/userApi";
import { UserReservationsResponse } from "../apis/reservationApi";

interface UserState {
  userReservations: UserReservationsResponse;
  errorCode: string;
  errorMessage: string;
  status: "idle" | "loading" | "succeeded" | "failed";
}

const initialState: UserState = {
  userReservations: [],
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
      );
  },
});

export const { clearUserError } = userSlice.actions;

export default userSlice.reducer;
