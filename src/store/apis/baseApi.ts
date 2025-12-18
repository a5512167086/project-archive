// src/services/baseApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type {
  BaseQueryFn,
  FetchArgs,
  FetchBaseQueryError
} from '@reduxjs/toolkit/query'
import { Mutex } from 'async-mutex'
import { CustomError } from '@/configs/type'

// 定義 LoginResponse 型別 (為了 refresh token 用)
interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

const mutex = new Mutex()

const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_BACKEND_URL,
  prepareHeaders: (headers) => {
    const token =
      localStorage.getItem('access_token') ||
      sessionStorage.getItem('access_token')
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    return headers
  }
})

const customBaseQuery: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  await mutex.waitForUnlock()
  let result = await baseQuery(args, api, extraOptions)

  // 攔截 401 或是特定 error code
  if (
    result.error &&
    (result.error.data as CustomError)?.error_code === 'TOKEN_EXPIRED'
  ) {
    if (!mutex.isLocked()) {
      const release = await mutex.acquire()
      try {
        const refreshToken =
          localStorage.getItem('refresh_token') ||
          sessionStorage.getItem('refresh_token')
        if (refreshToken) {
          const refreshResult = await baseQuery(
            {
              url: 'users/token-refresh',
              method: 'POST',
              body: { refresh_token: refreshToken }
            },
            api,
            extraOptions
          )

          if (refreshResult.data) {
            const data = refreshResult.data as LoginResponse
            const storage = localStorage.getItem('refresh_token')
              ? localStorage
              : sessionStorage
            storage.setItem('access_token', data.access_token)
            storage.setItem('refresh_token', data.refresh_token)

            // 重試原本的請求
            result = await baseQuery(args, api, extraOptions)
          } else {
            localStorage.clear()
            sessionStorage.clear()
            window.location.href = '/login'
          }
        } else {
          window.location.href = '/login'
        }
      } finally {
        release()
      }
    } else {
      await mutex.waitForUnlock()
      result = await baseQuery(args, api, extraOptions)
    }
  }
  return result
}

// 建立空的 API Slice，並定義 tagTypes
export const baseApi = createApi({
  reducerPath: 'api', // 整個 App 只會有這一個 reducerPath
  baseQuery: customBaseQuery,
  // 這裡先定義好所有可能的 Tag，讓子 Slice 可以使用
  tagTypes: [
    'Bot',
    'Brand',
    'User',
    'Category',
    'Ecomm',
    'Knowledge',
    'Module',
    'Product',
    'Order',
    'Reservation'
  ],
  endpoints: () => ({})
})
