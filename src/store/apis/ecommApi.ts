import { baseApi } from './baseApi'

export type ShippingOption = {
  method: 'home_delivery' | 'store_pickup'
  fee: number
  is_enabled: boolean
}

export type EcommResponse = {
  bot_uuid: string
  shipping_options: ShippingOption[]
}

export type CreateEcommRequest = {
  bot_uuid: string
  shipping_options: ShippingOption[]
}

export type UpdateEcommRequest = {
  bot_uuid: string
  shipping_options: ShippingOption[]
}

export type DeleteEcommRequest = {
  bot_uuid: string
  method: 'home_delivery' | 'store_pickup'
}

export const ecommApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getEcommSettings: builder.query<EcommResponse, string>({
      query: (botUuid) => ({
        url: `ecomm/${botUuid}`,
        method: 'GET'
      }),
      providesTags: ['Ecomm']
    }),
    createEcommSettings: builder.mutation<void, CreateEcommRequest>({
      query: (data) => ({
        url: `ecomm`,
        method: 'POST',
        body: data
      }),
      invalidatesTags: ['Ecomm']
    }),
    updateEcommSettings: builder.mutation<void, UpdateEcommRequest>({
      query: (data) => ({
        url: 'ecomm',
        method: 'PATCH',
        body: data
      }),
      invalidatesTags: ['Ecomm']
    }),
    deleteEcommShippingMethod: builder.mutation<void, DeleteEcommRequest>({
      query: (data) => ({
        url: 'ecomm',
        method: 'DELETE',
        body: data
      }),
      invalidatesTags: ['Ecomm']
    })
  })
})

export const {
  useLazyGetEcommSettingsQuery,
  useCreateEcommSettingsMutation,
  useUpdateEcommSettingsMutation,
  useDeleteEcommShippingMethodMutation
} = ecommApi
