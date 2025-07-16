import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { brandApi, Brand } from '../apis/brandApi'

interface BrandState {
  brandList: Brand[]
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: BrandState = {
  brandList: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const brandSlice = createSlice({
  name: 'brand',
  initialState,
  reducers: {
    initBrand: (state) => {
      state.brandList = []
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    },
    setBrandError: (state, action: PayloadAction<CustomError>) => {
      state.errorCode = action.payload.error_code
      state.errorMessage = action.payload.error_message
      state.status = 'failed'
    },
    clearBrandError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(brandApi.endpoints.getBrands.matchPending, (state) => {
        state.status = 'loading'
        state.errorCode = ''
        state.errorMessage = ''
      })
      .addMatcher(
        brandApi.endpoints.getBrands.matchFulfilled,
        (state, action) => {
          state.status = 'succeeded'
          state.brandList = action.payload
          state.errorCode = ''
          state.errorMessage = ''
        }
      )
      .addMatcher(
        brandApi.endpoints.getBrands.matchRejected,
        (state, action) => {
          state.status = 'failed'
          state.errorCode = action.error?.code || 'UNKNOWN_ERROR'
          state.errorMessage =
            action.error?.message || 'An unknown error occurred'
        }
      )
      .addMatcher(brandApi.endpoints.createBrand.matchFulfilled, (state) => {
        state.errorCode = ''
        state.errorMessage = ''
      })
      .addMatcher(brandApi.endpoints.updateBrand.matchFulfilled, (state) => {
        state.errorCode = ''
        state.errorMessage = ''
      })
      .addMatcher(brandApi.endpoints.deleteBrand.matchFulfilled, (state) => {
        state.errorCode = ''
        state.errorMessage = ''
      })
      .addMatcher(
        brandApi.endpoints.createBrand.matchRejected,
        (state, action) => {
          state.status = 'failed'
          state.errorCode = action.error?.code || 'CREATE_ERROR'
          state.errorMessage = action.error?.message || 'Failed to create brand'
        }
      )
      .addMatcher(
        brandApi.endpoints.updateBrand.matchRejected,
        (state, action) => {
          state.status = 'failed'
          state.errorCode = action.error?.code || 'UPDATE_ERROR'
          state.errorMessage = action.error?.message || 'Failed to update brand'
        }
      )
      .addMatcher(
        brandApi.endpoints.deleteBrand.matchRejected,
        (state, action) => {
          state.status = 'failed'
          state.errorCode = action.error?.code || 'DELETE_ERROR'
          state.errorMessage = action.error?.message || 'Failed to delete brand'
        }
      )
  }
})

export const { initBrand, setBrandError, clearBrandError } = brandSlice.actions

export default brandSlice.reducer
