import { baseApi } from './baseApi'

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

export const userApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    loginUser: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: 'users/login',
        method: 'POST',
        body: credentials
      }),
      invalidatesTags: ['User']
    }),
    oauthLoginUser: builder.mutation<LoginResponse, OAuthLoginRequest>({
      query: (oauthUser) => ({
        url: 'users/oauth-login',
        method: 'POST',
        body: oauthUser
      }),
      invalidatesTags: ['User']
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
      query: () => 'users/me',
      providesTags: ['User']
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
    }),
    refreshToken: builder.mutation<LoginResponse, { refresh_token: string }>({
      query: (body) => ({
        url: 'users/token-refresh',
        method: 'POST',
        body
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
  useResetPasswordMutation,
  useRefreshTokenMutation
} = userApi
