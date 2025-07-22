import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { categoryApi, Category } from '../apis/categoryApi'

interface CategoryState {
  categoryList: Category[]
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: CategoryState = {
  categoryList: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const categorySlice = createSlice({
  name: 'category',
  initialState,
  reducers: {
    setCategoryError: (state, action: PayloadAction<CustomError>) => {
      state.errorCode = action.payload.error_code
      state.errorMessage = action.payload.error_message
      state.status = 'failed'
    },
    clearCategoryError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        categoryApi.endpoints.getCategories.matchFulfilled,
        (state, action: PayloadAction<Category[]>) => {
          state.categoryList = action.payload
        }
      )
      .addMatcher(
        categoryApi.endpoints.getCategories.matchRejected,
        (state, action) => {
          const error = action.payload?.data as CustomError
          state.errorCode = error?.error_code
          state.errorMessage = error?.error_message
        }
      )
      .addMatcher(
        categoryApi.endpoints.createCategory.matchRejected,
        (state, action) => {
          const error = action.payload?.data as CustomError
          state.errorCode = error?.error_code
          state.errorMessage = error?.error_message
        }
      )
      .addMatcher(
        categoryApi.endpoints.updateCategory.matchRejected,
        (state, action) => {
          const error = action.payload?.data as CustomError
          state.errorCode = error?.error_code
          state.errorMessage = error?.error_message
        }
      )
      .addMatcher(
        categoryApi.endpoints.deleteCategory.matchRejected,
        (state, action) => {
          const error = action.payload?.data as CustomError
          state.errorCode = error?.error_code
          state.errorMessage = error?.error_message
        }
      )
  }
})

export const { setCategoryError, clearCategoryError } = categorySlice.actions

export default categorySlice.reducer
