import { createSlice } from "@reduxjs/toolkit";
import {
  reservationApi,
  ReservationItemsResponse,
  AvailableTimesResponse,
} from "../apis/reservationApi";

interface ReservationState {
  reservationItems: ReservationItemsResponse;
  availableTimes: AvailableTimesResponse;
  errorCode: string;
  errorMessage: string;
  status: "idle" | "loading" | "succeeded" | "failed";
}

const initialState: ReservationState = {
  reservationItems: [],
  availableTimes: [],
  errorCode: "",
  errorMessage: "",
  status: "idle",
};

export const reservationSlice = createSlice({
  name: "reservation",
  initialState,
  reducers: {
    clearReservationError: (state) => {
      state.errorCode = "";
      state.errorMessage = "";
      state.status = "idle";
    },
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        reservationApi.endpoints.getReservationItems.matchPending,
        (state) => {
          state.status = "loading";
        }
      )
      .addMatcher(
        reservationApi.endpoints.getReservationItems.matchFulfilled,
        (state, action) => {
          state.status = "succeeded";
          state.reservationItems = action.payload;
        }
      )
      .addMatcher(
        reservationApi.endpoints.getAvailableTimes.matchPending,
        (state) => {
          state.status = "loading";
        }
      )
      .addMatcher(
        reservationApi.endpoints.getAvailableTimes.matchFulfilled,
        (state, action) => {
          state.status = "succeeded";
          state.availableTimes = action.payload;
        }
      );
  },
});

export const { clearReservationError } = reservationSlice.actions;

export default reservationSlice.reducer;
