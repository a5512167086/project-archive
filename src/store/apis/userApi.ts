import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export enum OAuthProvider {
  Google = 'google',
  Line = 'line'
}

export type UserMeResponse = {
  username: string
  email: string
}

export type LoginRequest = {
  email: string
  password: string
  remember: boolean
}

export type LoginResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type RegisterRequest = {
  username: string
  email: string
  password: string
}

export type ForgotPasswordRequest = {
  email: string
}

export type ResetPasswordRequest = {
  token: string
  new_password: string
}

type ChangePasswordRequest = {
  old_password: string
  new_password: string
}

export type OAuthLoginRequest = {
  code: string
  provider: OAuthProvider
}

type OAuthBindRequest = {
  code: string
  provider: OAuthProvider
  action: 'bind' | 'unbind'
}

export type OAuthStatusResponse = {
  google: boolean
  line: boolean
}

export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_BACKEND_URL,
    prepareHeaders: (headers) => {
      if (!headers.has('Authorization')) {
        const access_token =
          localStorage.getItem('access_token') ||
          sessionStorage.getItem('access_token')
        if (access_token) {
          headers.set('Authorization', `Bearer ${access_token}`)
        }
      }
      return headers
    }
  }),
  endpoints: (builder) => ({
    loginUser: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: 'users/login',
        method: 'POST',
        body: credentials
      })
    }),
    oauthLoginUser: builder.mutation<LoginResponse, OAuthLoginRequest>({
      query: (oauthUser) => ({
        url: 'users/oauth-login',
        method: 'POST',
        body: oauthUser
      })
    }),
    oauthBindUser: builder.mutation<LoginResponse, OAuthBindRequest>({
      query: (oauthUser) => ({
        url: 'users/oauth-bind',
        method: 'POST',
        body: oauthUser
      })
    }),
    getOAuthStatus: builder.query<OAuthStatusResponse, void>({
      query: () => 'users/oauth-status'
    }),
    registerUser: builder.mutation<void, RegisterRequest>({
      query: (newUser) => ({
        url: 'users/register',
        method: 'POST',
        body: newUser
      })
    }),
    forgotPassword: builder.mutation<void, ForgotPasswordRequest>({
      query: (email) => ({
        url: 'users/forgot-password',
        method: 'POST',
        body: email
      })
    }),
    getUserMe: builder.query<UserMeResponse, void>({
      query: () => 'users/me'
    }),
    resetPassword: builder.mutation<void, ResetPasswordRequest>({
      query: (data) => ({
        url: 'users/reset-password',
        method: 'POST',
        body: data,
        headers: { Authorization: `Bearer ${data.token}` }
      })
    }),
    changePassword: builder.mutation<void, ChangePasswordRequest>({
      query: (data) => ({
        url: 'users/change-password',
        method: 'POST',
        body: data
      })
    })
  })
})

export const {
  useLoginUserMutation,
  useOauthLoginUserMutation,
  useOauthBindUserMutation,
  useLazyGetOAuthStatusQuery,
  useRegisterUserMutation,
  useChangePasswordMutation,
  useForgotPasswordMutation,
  useLazyGetUserMeQuery,
  useResetPasswordMutation
} = userApi
