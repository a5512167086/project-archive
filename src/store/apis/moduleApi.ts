import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export type ModuleSetting = {
  module_id: string
  class_id: number
  object_id: number
  chinese_name: string
  is_enabled: boolean
  version: string
  description: string
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
    baseUrl: import.meta.env.VITE_MODULE_BACKEND_URL,
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
    getModuleSettings: builder.query<ModuleSetting[], GetModuleSettingsRequest>(
      {
        query: (data) => ({
          url: `module-setting/${data.bot_class_id}`,
          method: 'GET'
        })
      }
    ),
    insertModuleSetting: builder.mutation<void, InsertModuleSettingsRequest>({
      query: (data) => ({
        url: `module-setting`,
        method: 'POST',
        body: data
      })
    })
  })
})

export const { useLazyGetModuleSettingsQuery, useInsertModuleSettingMutation } =
  moduleApi
