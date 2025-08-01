import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { ecommApi, EcommResponse } from '../apis/ecommApi'

interface EcommState {
  shippingOptions: EcommResponse['shipping_options']
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: EcommState = {
  shippingOptions: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const ecommSlice = createSlice({
  name: 'ecomm',
  initialState,
  reducers: {
    clearEcommError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        ecommApi.endpoints.getEcommSettings.matchFulfilled,
        (state, action: PayloadAction<EcommResponse>) => {
          state.shippingOptions = action.payload.shipping_options
          state.status = 'succeeded'
        }
      )
      .addMatcher(ecommApi.endpoints.getEcommSettings.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(
        ecommApi.endpoints.getEcommSettings.matchRejected,
        (state, action) => {
          const error = action.payload?.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code
          state.errorMessage = error?.error_message
        }
      )
      .addMatcher(
        ecommApi.endpoints.updateEcommSettings.matchFulfilled,
        (state) => {
          state.status = 'succeeded'
        }
      )
      .addMatcher(
        ecommApi.endpoints.updateEcommSettings.matchRejected,
        (state, action) => {
          const error = action.payload?.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code
          state.errorMessage = error?.error_message
        }
      )
      .addMatcher(
        ecommApi.endpoints.deleteEcommShippingMethod.matchFulfilled,
        (state) => {
          state.status = 'succeeded'
        }
      )
      .addMatcher(
        ecommApi.endpoints.deleteEcommShippingMethod.matchRejected,
        (state, action) => {
          const error = action.payload?.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code
          state.errorMessage = error?.error_message
        }
      )
  }
})

export const { clearEcommError } = ecommSlice.actions

export default ecommSlice.reducer
