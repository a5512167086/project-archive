import { createSlice } from '@reduxjs/toolkit'
import { moduleApi, ModuleSetting } from '../apis/moduleApi'
import { CustomError } from '@/configs/type'

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
  reducers: {
    clearModuleError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        moduleApi.endpoints.getModuleSettings.matchPending,
        (state) => {
          state.status = 'loading'
        }
      )
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
          const error = action.payload!.data as CustomError
          state.status = 'failed'
          state.errorCode = error['error_code']
          state.errorMessage = error['error_message']
        }
      )
  }
})

export const { clearModuleError } = moduleSlice.actions

export default moduleSlice.reducer
