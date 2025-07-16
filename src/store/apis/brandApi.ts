import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export type Brand = {
  object_id: number
  brand_name: string
  brand_description: string
}

export type BrandsResponse = Brand[]

export type CreateBrandRequest = {
  bot_uuid: string
  brand_name: string
  brand_description: string
}

export type UpdateBrandRequest = {
  bot_uuid: string
  object_id: number
  brand_name: string
  brand_description: string
}

export type DeleteBrandRequest = {
  bot_uuid: string
  deleted_id_list: number[]
}

export const brandApi = createApi({
  reducerPath: 'brandApi',
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
  tagTypes: ['Brand'],
  endpoints: (builder) => ({
    getBrands: builder.query<BrandsResponse, string>({
      query: (botUuid) => ({
        url: `brands/${botUuid}`,
        method: 'GET'
      }),
      providesTags: ['Brand']
    }),
    createBrand: builder.mutation<void, CreateBrandRequest>({
      query: (brand) => ({
        url: 'brands',
        method: 'POST',
        body: brand
      }),
      invalidatesTags: ['Brand']
    }),
    updateBrand: builder.mutation<void, UpdateBrandRequest>({
      query: (brand) => ({
        url: 'brands',
        method: 'PATCH',
        body: brand
      }),
      invalidatesTags: ['Brand']
    }),
    deleteBrand: builder.mutation<void, DeleteBrandRequest>({
      query: (deleteRequest) => ({
        url: 'brands',
        method: 'DELETE',
        body: deleteRequest
      }),
      invalidatesTags: ['Brand']
    })
  })
})

export const {
  useGetBrandsQuery,
  useLazyGetBrandsQuery,
  useCreateBrandMutation,
  useUpdateBrandMutation,
  useDeleteBrandMutation
} = brandApi
