import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { brandApi, Brand } from '../apis/brandApi'

interface BrandState {
  brandList: Brand[]
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
  successMessage: string
  successType: 'create' | 'update' | 'delete' | null
}

const initialState: BrandState = {
  brandList: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle',
  successMessage: '',
  successType: null
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
    },
    clearBrandSuccess: (state) => {
      state.successMessage = ''
      state.successType = null
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(brandApi.endpoints.getBrands.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(
        brandApi.endpoints.getBrands.matchFulfilled,
        (state, action) => {
          state.status = 'succeeded'
          state.brandList = action.payload
        }
      )
      .addMatcher(
        brandApi.endpoints.getBrands.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error['error_code']
          state.errorMessage = error['error_message']
        }
      )
      .addMatcher(brandApi.endpoints.createBrand.matchFulfilled, (state) => {
        state.status = 'succeeded'
      })
      .addMatcher(brandApi.endpoints.updateBrand.matchFulfilled, (state) => {
        state.status = 'succeeded'
      })
      .addMatcher(brandApi.endpoints.deleteBrand.matchFulfilled, (state) => {
        state.status = 'succeeded'
      })
      .addMatcher(
        brandApi.endpoints.createBrand.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error['error_code']
          state.errorMessage = error['error_message']
        }
      )
      .addMatcher(
        brandApi.endpoints.updateBrand.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error['error_code']
          state.errorMessage = error['error_message']
        }
      )
      .addMatcher(
        brandApi.endpoints.deleteBrand.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error['error_code']
          state.errorMessage = error['error_message']
        }
      )
  }
})

export const { initBrand, setBrandError, clearBrandError } = brandSlice.actions

export default brandSlice.reducer
