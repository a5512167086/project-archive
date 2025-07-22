import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export interface Category {
  parent_class_id: number | null
  class_id: number
  category_name: string
  category_description: string
  children: Category[]
}

export type CategoriesResponse = Category[]

export type CreateCategoryRequest = {
  bot_uuid: string
  category_name: string
  category_description: string
  parent_category_id?: number
}

export type UpdateCategoryRequest = {
  bot_uuid: string
  class_id: number
  category_name?: string
  category_description?: string
  parent_category_id?: number | null
}

export type DeleteCategoryRequest = {
  bot_uuid: string
  deleted_class_id_list: number[]
}

export const categoryApi = createApi({
  reducerPath: 'categoryApi',
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
  tagTypes: ['Category'],
  endpoints: (builder) => ({
    getCategories: builder.query<CategoriesResponse, string>({
      query: (botUuid) => `categories/${botUuid}`,
      providesTags: ['Category']
    }),
    createCategory: builder.mutation<void, CreateCategoryRequest>({
      query: (category) => ({
        url: 'categories',
        method: 'POST',
        body: category
      }),
      invalidatesTags: ['Category']
    }),
    updateCategory: builder.mutation<void, UpdateCategoryRequest>({
      query: (category) => ({
        url: 'categories',
        method: 'PATCH',
        body: category
      }),
      invalidatesTags: ['Category']
    }),
    deleteCategory: builder.mutation<void, DeleteCategoryRequest>({
      query: (deleteRequest) => ({
        url: 'categories',
        method: 'DELETE',
        body: deleteRequest
      }),
      invalidatesTags: ['Category']
    })
  })
})

export const {
  useLazyGetCategoriesQuery,
  useCreateCategoryMutation,
  useUpdateCategoryMutation,
  useDeleteCategoryMutation
} = categoryApi
