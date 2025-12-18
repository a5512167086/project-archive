import { baseApi } from './baseApi' 

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

export const categoryApi = baseApi.injectEndpoints({
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
