import { createSlice } from '@reduxjs/toolkit'
import { clearUserToken } from '@/utils/helper'
import { searchApi, SearchItem } from '../apis/searchApi'

interface SearchState {
  searchItems: SearchItem[]
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: SearchState = {
  searchItems: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {},
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
          clearUserToken()
          state.status = 'failed'
          state.errorCode = action.error.code!
          state.errorMessage = action.error.message!
        }
      )
  }
})

export default searchSlice.reducer
