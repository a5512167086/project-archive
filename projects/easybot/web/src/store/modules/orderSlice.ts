import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { GetOrdersResponse, orderApi } from '../apis/orderApi'

interface OrderState {
  orders: GetOrdersResponse[]
  currentOrderObjectId: number | null
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: OrderState = {
  orders: [],
  currentOrderObjectId: null,
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const orderSlice = createSlice({
  name: 'orderSlice',
  initialState,
  reducers: {
    clearOrderError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(orderApi.endpoints.getOrders.matchPending, (state) => {
        state.status = 'loading'
        state.errorMessage = ''
        state.errorCode = ''
      })
      .addMatcher(
        orderApi.endpoints.getOrders.matchFulfilled,
        (state, action: PayloadAction<GetOrdersResponse[]>) => {
          state.status = 'succeeded'
          state.orders = action.payload
        }
      )
      .addMatcher(
        orderApi.endpoints.getOrders.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
  }
})

export const { clearOrderError } = orderSlice.actions

export default orderSlice.reducer