import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export type GetSearchItemsRequest = {
  bot_class_id: number
}

type InsertSearchItemRequest = {
  bot_class_id: number
  item_name: string
  item_english_name: string
  item_type: string
  item_description: string
  item_price: string
  item_instruction: string
  item_ingredient: string
  item_url?: string
}

type InsertSearchItemsByUrlRequest = {
  bot_class_id: number
  url: string
}

type DeleteSearchItemsRequest = {
  bot_class_id: number
  deleted_id_list: number[]
}

interface Image {
  image_src: string
  ocr_text: string
}

export type SearchItem = {
  search_text_id: string
  class_id: number
  object_id: number
  chinese_name: string
  english_name: string
  type: string
  description: string
  price: string
  instruction: string
  ingredient: string
  url: string
  images: Image[]
}

export const searchApi = createApi({
  reducerPath: 'searchApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_BACKEND_URL,
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
    getSearchItems: builder.query<SearchItem[], GetSearchItemsRequest>({
      query: (search) => ({
        url: `search-items/${search.bot_class_id}`,
        method: 'GET'
      })
    }),
    insertSearchItem: builder.mutation<void, InsertSearchItemRequest>({
      query: (data) => ({
        url: `search-item`,
        method: 'POST',
        body: data
      })
    }),
    insertSearchItemsByUrl: builder.mutation<
      void,
      InsertSearchItemsByUrlRequest
    >({
      query: (data) => ({
        url: `search-items`,
        method: 'POST',
        body: data
      })
    }),
    deleteSearchItems: builder.mutation<void, DeleteSearchItemsRequest>({
      query: (data) => ({
        url: `search-items`,
        method: 'DELETE',
        body: data
      })
    })
  })
})

export const {
  useLazyGetSearchItemsQuery,
  useInsertSearchItemMutation,
  useInsertSearchItemsByUrlMutation,
  useDeleteSearchItemsMutation
} = searchApi
