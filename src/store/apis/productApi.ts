import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
export type ProductImageResponse = {
  image_id: number
  image_url: string
  object_id: number
  display_order: number
}

export type ProductVariantResponse = {
  variant_id: string
  object_id: number
  variant_name: string
  sku_code: string | null
  price: number | null
  stock: number
  created_at: Date
  updated_at: Date
}

export type GetProductsResponse = {
  product_id: string
  object_id: number
  product_name: string
  product_description: string | null
  brand_id: number | null
  category_id: number | null
  sku_code: string
  price: number | null
  stock: number | null
  is_active: boolean
  created_at: Date
  updated_at: Date
  images?: ProductImageResponse[]
  variants?: ProductVariantResponse[]
}

type GetProductsRequest = {
  bot_uuid: string
}

export type CreateProductRequest = {
  bot_uuid: string
  product_name: string
  product_description: string
  sku_code: string
  price: number
  stock: number
  is_active: boolean
  category_id?: number | null
  brand_id?: number | null
  images: File[] | null
}

type DeleteProductsRequest = {
  bot_uuid: string
  product_ids: string[]
}

export const productApi = createApi({
  reducerPath: 'productApi',
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
    getProducts: builder.query<GetProductsResponse[], GetProductsRequest>({
      query: (data) => ({
        url: `products/${data.bot_uuid}`,
        method: 'GET'
      })
    }),
    createProducts: builder.mutation<void, CreateProductRequest>({
      query: (data) => {
        const bodyFormData = new FormData()
        bodyFormData.append('bot_uuid', data.bot_uuid)
        bodyFormData.append('product_name', data.product_name)
        bodyFormData.append('product_description', data.product_description)
        bodyFormData.append('sku_code', data.sku_code)
        bodyFormData.append('price', data.price.toString())
        bodyFormData.append('stock', data.stock.toString())
        bodyFormData.append('is_active', data.is_active.toString())
        bodyFormData.append('category_id', data.category_id?.toString() || '')
        bodyFormData.append('brand_id', data.brand_id?.toString() || '')
        data.images?.forEach((file) => {
          bodyFormData.append('images', file)
        })

        return {
          url: 'products',
          method: 'POST',
          body: bodyFormData,
          formData: true
        }
      }
    }),
    deleteProducts: builder.mutation<void, DeleteProductsRequest>({
      query: (data) => ({
        url: 'products',
        method: 'DELETE',
        body: data
      })
    })
  })
})

export const {
  useLazyGetProductsQuery,
  useCreateProductsMutation,
  useDeleteProductsMutation
} = productApi
