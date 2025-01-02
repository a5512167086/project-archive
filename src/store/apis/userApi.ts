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
  token: string
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

export type OAuthLoginRequest = {
  code: string
  provider: OAuthProvider
}

export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_USER_BACKEND_URL,
    prepareHeaders: (headers) => {
      if (!headers.has('Authorization')) {
        const token =
          localStorage.getItem('token') || sessionStorage.getItem('token')
        if (token) {
          headers.set('Authorization', `Bearer ${token}`)
        }
      }
      return headers
    }
  }),
  endpoints: (builder) => ({
    loginUser: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: 'user/login',
        method: 'POST',
        body: credentials
      })
    }),
    oauthLoginUser: builder.mutation<LoginResponse, OAuthLoginRequest>({
      query: (oauthUser) => ({
        url: 'user/oauth_login',
        method: 'POST',
        body: oauthUser
      })
    }),
    registerUser: builder.mutation<void, RegisterRequest>({
      query: (newUser) => ({
        url: 'user/register',
        method: 'POST',
        body: newUser
      })
    }),
    forgotPassword: builder.mutation<void, ForgotPasswordRequest>({
      query: (email) => ({
        url: 'user/forgot_password',
        method: 'POST',
        body: email
      })
    }),
    getUserMe: builder.query<UserMeResponse, void>({
      query: () => 'user/me'
    }),
    resetPassword: builder.mutation<void, ResetPasswordRequest>({
      query: (data) => ({
        url: 'user/reset_password',
        method: 'POST',
        body: data,
        headers: { Authorization: `Bearer ${data.token}` }
      })
    })
  })
})

export const {
  useLoginUserMutation,
  useOauthLoginUserMutation,
  useRegisterUserMutation,
  useForgotPasswordMutation,
  useLazyGetUserMeQuery,
  useResetPasswordMutation
} = userApi
