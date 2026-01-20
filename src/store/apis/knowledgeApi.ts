import { baseApi } from './baseApi'

export type KnowledgeItem = {
  class_id: number
  object_id: number
  question: string
  answer: string
}

export type SyncStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export type KnowledgeSyncStatusResponse = {
  bot_uuid: string
  status: SyncStatus
  has_pending_changes: boolean
  last_sync_start_time: string | null
  last_sync_end_time: string | null
  last_successful_sync_time: string | null
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

type TriggerSyncRequest = {
  bot_uuid: string
}

type GetSyncStatusRequest = {
  bot_uuid: string
}

export const knowledgeApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getKnowledgeItems: builder.query<KnowledgeItem[], GetKnowledgeItemsRequest>(
      {
        query: (data) => ({
          url: `knowledges/${data.bot_uuid}`,
          method: 'GET'
        }),
        providesTags: ['Knowledge']
      }
    ),
    insertKnowledgeItem: builder.mutation<void, InsertKnowledgeItemRequest>({
      query: (data) => ({
        url: `knowledges`,
        method: 'POST',
        body: data
      }),
      invalidatesTags: ['Knowledge']
    }),
    updateKnowledgeItem: builder.mutation<void, UpdateKnowledgeItemRequest>({
      query: (data) => ({
        url: `knowledges`,
        method: 'PATCH',
        body: data
      }),
      invalidatesTags: ['Knowledge']
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
      },
      invalidatesTags: ['Knowledge']
    }),
    deleteKnowledgeItems: builder.mutation<void, DeleteKnowledgeItemsRequest>({
      query: (data) => ({
        url: `knowledges`,
        method: 'DELETE',
        body: data
      }),
      invalidatesTags: ['Knowledge']
    }),
    getSyncStatus: builder.query<
      KnowledgeSyncStatusResponse,
      GetSyncStatusRequest
    >({
      query: (data) => ({
        url: `knowledges/${data.bot_uuid}/sync-status`,
        method: 'GET'
      }),
      providesTags: ['Knowledge']
    }),

    triggerSync: builder.mutation<void, TriggerSyncRequest>({
      query: (data) => ({
        url: `knowledges/sync`,
        method: 'POST',
        body: data
      }),
      invalidatesTags: ['Knowledge']
    })
  })
})

export const {
  useLazyGetKnowledgeItemsQuery,
  useInsertKnowledgeItemMutation,
  useInsertKnowledgeItemsByCSVMutation,
  useDeleteKnowledgeItemsMutation,
  useUpdateKnowledgeItemMutation,
  useGetSyncStatusQuery,
  useTriggerSyncMutation
} = knowledgeApi
