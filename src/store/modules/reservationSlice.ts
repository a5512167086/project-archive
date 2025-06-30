import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import {
  reservationApi,
  ReservationItemsResponse
} from '../apis/reservationApi'

interface ReservationState {
  reservationItems: ReservationItemsResponse[]
  currentReservationItemObjectId: number | null
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: ReservationState = {
  reservationItems: [],
  currentReservationItemObjectId: null,
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const reservationSlice = createSlice({
  name: 'reservation',
  initialState,
  reducers: {
    setCurrentReservationItemObjectId(
      state,
      action: PayloadAction<number | null>
    ) {
      state.currentReservationItemObjectId = action.payload
    },
    clearReservationError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        reservationApi.endpoints.getServices.matchPending,
        (state) => {
          state.status = 'loading'
          state.errorMessage = ''
          state.errorCode = ''
        }
      )
      .addMatcher(
        reservationApi.endpoints.getServices.matchFulfilled,
        (state, action: PayloadAction<ReservationItemsResponse[]>) => {
          state.status = 'succeeded'
          state.reservationItems = action.payload
        }
      )
      .addMatcher(
        reservationApi.endpoints.getServices.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
      .addMatcher(
        reservationApi.endpoints.insertService.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
      .addMatcher(
        reservationApi.endpoints.patchReservationItem.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
      .addMatcher(
        reservationApi.endpoints.deleteReservationItems.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
  }
})

export const { setCurrentReservationItemObjectId, clearReservationError } =
  reservationSlice.actions

export default reservationSlice.reducer
