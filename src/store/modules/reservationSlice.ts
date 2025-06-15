import { createSlice, PayloadAction } from '@reduxjs/toolkit'
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
          state.status = 'failed'
          state.errorMessage = action.error?.message || '取得失敗'
          state.errorCode = action.error?.name || 'ERROR'
        }
      )
  }
})

export const { setCurrentReservationItemObjectId } = reservationSlice.actions

export default reservationSlice.reducer
