import { baseApi } from './baseApi'

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
  bot_uuid: string
}

type InsertModuleSettingsRequest = {
  bot_uuid: string
  module_name: string
  is_enabled: boolean
}

export const moduleApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getModuleSettings: builder.query<ModuleSetting[], GetModuleSettingsRequest>(
      {
        query: (data) => ({
          url: `modules/${data.bot_uuid}`,
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
