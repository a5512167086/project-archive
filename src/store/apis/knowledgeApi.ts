import { baseApi } from './baseApi'

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

type UpdateKnowledgeItemRequest = {
  bot_uuid: string
  object_id: number
  question: string
  answer: string
}

export const knowledgeApi = baseApi.injectEndpoints({
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
    updateKnowledgeItem: builder.mutation<void, UpdateKnowledgeItemRequest>({
      query: (data) => ({
        url: `knowledges`,
        method: 'PATCH',
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
  useDeleteKnowledgeItemsMutation,
  useUpdateKnowledgeItemMutation
} = knowledgeApi
