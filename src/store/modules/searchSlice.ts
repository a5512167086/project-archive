import { createSlice } from '@reduxjs/toolkit'
import { searchApi, SearchItem } from '../apis/searchApi'

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
          state.status = 'failed'
          state.errorCode = action.error.code!
          state.errorMessage = action.error.message!
        }
      )
  }
})

export const { setCurrentSearchItem, clearCurrentSearchItem } =
  searchSlice.actions

export default searchSlice.reducer
