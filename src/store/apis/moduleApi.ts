import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export type ModuleSetting = {
  module_id: string
  class_id: number
  object_id: number
  chinese_name: string
  is_enabled: boolean
  version: string
  description: string | null
}

type GetModuleSettingsRequest = {
  bot_class_id: number
}

type InsertModuleSettingsRequest = {
  bot_class_id: number
  module_name: string
  is_enabled: boolean
}

export const moduleApi = createApi({
  reducerPath: 'moduleApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_BACKEND_URL,
    prepareHeaders: (headers) => {
      if (!headers.has('Authorization')) {
        const token =
          localStorage.getItem('access_token') ||
          sessionStorage.getItem('access_token')
        if (token) {
          headers.set('Authorization', `Bearer ${token}`)
        }
      }
      return headers
    }
  }),
  endpoints: (builder) => ({
    getModuleSettings: builder.query<ModuleSetting[], GetModuleSettingsRequest>(
      {
        query: (data) => ({
          url: `modules/${data.bot_class_id}`,
          method: 'GET'
        })
      }
    ),
    insertModuleSetting: builder.mutation<void, InsertModuleSettingsRequest>({
      query: (data) => ({
        url: `modules`,
        method: 'POST',
        body: data
      })
    })
  })
})

export const { useGetModuleSettingsQuery, useInsertModuleSettingMutation } =
  moduleApi
