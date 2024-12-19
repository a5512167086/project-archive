import { createSlice } from '@reduxjs/toolkit'
import { clearUserToken } from '@/utils/helper'
import { moduleApi, ModuleSetting } from '../apis/moduleApi'

interface ModuleState {
  moduleSettings: ModuleSetting[]
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: ModuleState = {
  moduleSettings: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const moduleSlice = createSlice({
  name: 'module',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addMatcher(moduleApi.endpoints.getModuleSettings.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(
        moduleApi.endpoints.getModuleSettings.matchFulfilled,
        (state, action) => {
          state.status = 'succeeded'
          state.moduleSettings = action.payload
        }
      )
      .addMatcher(
        moduleApi.endpoints.getModuleSettings.matchRejected,
        (state, action) => {
          clearUserToken()
          state.status = 'failed'
          state.errorCode = action.error.code!
          state.errorMessage = action.error.message!
        }
      )
  }
})

export default moduleSlice.reducer
