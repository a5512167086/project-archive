import { createSlice } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { userApi } from '../apis/userApi'
import { clearUserToken } from '@/utils/helper'

interface UserState {
  username: string
  email: string
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: UserState = {
  username: '',
  email: '',
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    clearUserError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    },
    initUser: (state) => {
      state.username = ''
      state.email = ''
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(userApi.endpoints.getUserMe.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(
        userApi.endpoints.getUserMe.matchFulfilled,
        (state, action) => {
          state.status = 'succeeded'
          state.username = action.payload.username
          state.email = action.payload.email
        }
      )
      .addMatcher(
        userApi.endpoints.getUserMe.matchRejected,
        (state, action) => {
          clearUserToken()
          state.status = 'failed'
          const error = action.payload!.data as CustomError
          state.errorCode = error!.error_code
          state.errorMessage = error!.error_message
        }
      )
      .addMatcher(
        userApi.endpoints.forgotPassword.matchRejected,
        (state, action) => {
          state.status = 'failed'
          const error = action.payload!.data as CustomError
          state.errorCode = error!.error_code
          state.errorMessage = error!.error_message
        }
      )
      .addMatcher(
        userApi.endpoints.registerUser.matchRejected,
        (state, action) => {
          state.status = 'failed'
          const error = action.payload!.data as CustomError
          state.errorCode = error!.error_code
          state.errorMessage = error!.error_message
        }
      )
      .addMatcher(
        userApi.endpoints.loginUser.matchRejected,
        (state, action) => {
          state.status = 'failed'
          const error = action.payload!.data as CustomError
          state.errorCode = error!.error_code
          state.errorMessage = error!.error_message
        }
      )
      .addMatcher(
        userApi.endpoints.oauthLoginUser.matchRejected,
        (state, action) => {
          state.status = 'failed'
          const error = action.payload!.data as CustomError
          state.errorCode = error!.error_code
          state.errorMessage = error!.error_message
        }
      )
      .addMatcher(
        userApi.endpoints.changePassword.matchRejected,
        (state, action) => {
          state.status = 'failed'
          const error = action.payload!.data as CustomError
          state.errorCode = error!.error_code
          state.errorMessage = error!.error_message
        }
      )
  }
})

export const { clearUserError, initUser } = userSlice.actions

export default userSlice.reducer
