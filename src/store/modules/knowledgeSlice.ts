import { createSlice } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { knowledgeApi, KnowledgeItem } from '../apis/knowledgeApi'

interface KnowledgeState {
  knowledgeItems: KnowledgeItem[]
  currentknowledgeItemObjectId: number | null
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: KnowledgeState = {
  knowledgeItems: [],
  currentknowledgeItemObjectId: null,
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const knowledgeSlice = createSlice({
  name: 'knowledge',
  initialState,
  reducers: {
    setCurrentKnowledgeItem: (state, action) => {
      state.currentknowledgeItemObjectId = action.payload
    },
    clearCurrentKnowledgeItem: (state) => {
      state.currentknowledgeItemObjectId = null
    },
    clearKnowledgeError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        knowledgeApi.endpoints.getKnowledgeItems.matchPending,
        (state) => {
          state.status = 'loading'
        }
      )
      .addMatcher(
        knowledgeApi.endpoints.getKnowledgeItems.matchFulfilled,
        (state, action) => {
          state.status = 'succeeded'
          state.knowledgeItems = action.payload
        }
      )
      .addMatcher(
        knowledgeApi.endpoints.getKnowledgeItems.matchRejected,
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
  setCurrentKnowledgeItem,
  clearCurrentKnowledgeItem,
  clearKnowledgeError
} = knowledgeSlice.actions

export default knowledgeSlice.reducer
