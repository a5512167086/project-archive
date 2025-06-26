import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export type KnowledgeItem = {
  class_id: number
  object_id: number
  question: string
  answer: string
}

type GetKnowledgeItemsRequest = {
  bot_uuid: string
}

type InsertKnowledgeItemRequest = {
  bot_uuid: string
  question: string
  answer: string
}

type InsertKnowledgeItemsRequest = {
  bot_uuid: string
  csv_file: File
}

type DeleteKnowledgeItemsRequest = {
  bot_uuid: string
  deleted_id_list: number[]
}

export const knowledgeApi = createApi({
  reducerPath: 'knowledgeApi',
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
    getKnowledgeItems: builder.query<KnowledgeItem[], GetKnowledgeItemsRequest>(
      {
        query: (data) => ({
          url: `knowledges/${data.bot_uuid}`,
          method: 'GET'
        })
      }
    ),
    insertKnowledgeItem: builder.mutation<void, InsertKnowledgeItemRequest>({
      query: (data) => ({
        url: `knowledges`,
        method: 'POST',
        body: data
      })
    }),
    insertKnowledgeItemsByCSV: builder.mutation<
      void,
      InsertKnowledgeItemsRequest
    >({
      query: (data) => {
        const formData = new FormData()
        formData.append('bot_uuid', data.bot_uuid)
        formData.append('csv_file', data.csv_file)

        return {
          url: `knowledges/upload`,
          method: 'POST',
          body: formData
        }
      }
    }),
    deleteKnowledgeItems: builder.mutation<void, DeleteKnowledgeItemsRequest>({
      query: (data) => ({
        url: `knowledges`,
        method: 'DELETE',
        body: data
      })
    })
  })
})

export const {
  useLazyGetKnowledgeItemsQuery,
  useInsertKnowledgeItemMutation,
  useInsertKnowledgeItemsByCSVMutation,
  useDeleteKnowledgeItemsMutation
} = knowledgeApi
