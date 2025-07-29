import { createSlice } from '@reduxjs/toolkit'
import { productApi, GetProductsResponse } from '../apis/productApi'
import { CustomError } from '@/configs/type'

interface ProductState {
  products: GetProductsResponse[]
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: ProductState = {
  products: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const productSlice = createSlice({
  name: 'product',
  initialState,
  reducers: {
    clearProductError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(productApi.endpoints.getProducts.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(
        productApi.endpoints.getProducts.matchFulfilled,
        (state, action) => {
          state.status = 'succeeded'
          state.products = action.payload
        }
      )
      .addMatcher(
        productApi.endpoints.getProducts.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error['error_code']
          state.errorMessage = error['error_message']
        }
      )
      .addMatcher(
        productApi.endpoints.createProducts.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
      .addMatcher(
        productApi.endpoints.updateProduct.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
      .addMatcher(
        productApi.endpoints.deleteProducts.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error?.error_code || 'UNKNOWN_ERROR'
          state.errorMessage = error?.error_message || 'Unknown error occurred'
        }
      )
  }
})

export const { clearProductError } = productSlice.actions

export default productSlice.reducer
