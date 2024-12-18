import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export type GetSearchItemsRequest = {
  bot_class_id: number
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
    baseUrl: import.meta.env.VITE_SEARCH_BACKEND_URL,
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
    })
  })
})

export const { useLazyGetSearchItemsQuery } = searchApi
