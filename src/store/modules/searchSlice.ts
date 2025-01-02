import { createSlice } from '@reduxjs/toolkit'
import { searchApi, SearchItem } from '../apis/searchApi'
import { CustomError } from '@/configs/type'

interface SearchState {
  searchItems: SearchItem[]
  currentSearchItemObjectId: number | null
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: SearchState = {
  searchItems: [],
  currentSearchItemObjectId: null,
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setCurrentSearchItem: (state, action) => {
      state.currentSearchItemObjectId = action.payload
    },
    clearCurrentSearchItem: (state) => {
      state.currentSearchItemObjectId = null
    },
    clearSearchError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(searchApi.endpoints.getSearchItems.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(
        searchApi.endpoints.getSearchItems.matchFulfilled,
        (state, action) => {
          state.status = 'succeeded'
          state.searchItems = action.payload
        }
      )
      .addMatcher(
        searchApi.endpoints.getSearchItems.matchRejected,
        (state, action) => {
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error['error_code']
          state.errorMessage = error['error_message']
        }
      )
  }
})

export const {
  setCurrentSearchItem,
  clearCurrentSearchItem,
  clearSearchError
} = searchSlice.actions

export default searchSlice.reducer
