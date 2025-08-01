import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

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

export const ecommApi = createApi({
  reducerPath: 'ecommApi',
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
  tagTypes: ['Ecomm'],
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
