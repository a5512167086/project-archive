import { baseApi } from './baseApi'

export type KnowledgeItem = {
  class_id: number
  object_id: number
  question: string
  answer: string
}

export type KnowledgeFileItem = {
  class_id: number
  object_id: number
  file_id: number
  filename: string
  display_name: string
  file_type: string
  created_at: string
}

export type SyncStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export type KnowledgeSyncStatusResponse = {
  bot_uuid: string
  status: SyncStatus
  has_pending_changes: boolean
}

export type InsertKnowledgeItemRequest = {
  bot_uuid: string
  question: string
  answer: string
}

export type InsertKnowledgeItemsByCSVRequest = {
  bot_uuid: string
  csv_file: File
}

export type UpdateKnowledgeItemRequest = {
  bot_uuid: string
  object_id: number
  question: string
  answer: string
}

export type DeleteKnowledgeItemsRequest = {
  bot_uuid: string
  deleted_id_list: number[]
}

export type InsertKnowledgeFilesRequest = {
  bot_uuid: string
  files: File[]
}

export type UpdateKnowledgeFileRequest = {
  bot_uuid: string
  file_id: number
  display_name: string
}

export type DeleteKnowledgeFilesRequest = {
  bot_uuid: string
  file_id_list: number[]
}

export const knowledgeApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getKnowledgeItems: builder.query<KnowledgeItem[], { bot_uuid: string }>({
      query: (data) => `knowledges/${data.bot_uuid}`,
      providesTags: ['Knowledge']
    }),
    insertKnowledgeItem: builder.mutation<void, InsertKnowledgeItemRequest>({
      query: (data) => ({ url: 'knowledges', method: 'POST', body: data }),
      invalidatesTags: ['Knowledge']
    }),
    insertKnowledgeItemsByCSV: builder.mutation<
      void,
      InsertKnowledgeItemsByCSVRequest
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
    updateKnowledgeItem: builder.mutation<void, UpdateKnowledgeItemRequest>({
      query: (data) => ({ url: 'knowledges', method: 'PATCH', body: data }),
      invalidatesTags: ['Knowledge']
    }),
    deleteKnowledgeItems: builder.mutation<void, DeleteKnowledgeItemsRequest>({
      query: (data) => ({ url: 'knowledges', method: 'DELETE', body: data }),
      invalidatesTags: ['Knowledge']
    }),
    getKnowledgeFiles: builder.query<KnowledgeFileItem[], { bot_uuid: string }>(
      {
        query: (data) => `knowledges/files/${data.bot_uuid}`,
        providesTags: ['Knowledge']
      }
    ),
    insertKnowledgeFiles: builder.mutation<void, InsertKnowledgeFilesRequest>({
      query: (data) => {
        const formData = new FormData()
        formData.append('bot_uuid', data.bot_uuid)
        data.files.forEach((f) => formData.append('files', f))
        return { url: `knowledges/files`, method: 'POST', body: formData }
      },
      invalidatesTags: ['Knowledge']
    }),
    updateKnowledgeFile: builder.mutation<void, UpdateKnowledgeFileRequest>({
      query: (data) => ({
        url: `knowledges/files`,
        method: 'PATCH',
        body: data
      }),
      invalidatesTags: ['Knowledge']
    }),
    deleteKnowledgeFiles: builder.mutation<void, DeleteKnowledgeFilesRequest>({
      query: (data) => ({
        url: `knowledges/files`,
        method: 'DELETE',
        body: data
      }),
      invalidatesTags: ['Knowledge']
    }),
    downloadKnowledgeFile: builder.query<
      Blob,
      { bot_uuid: string; file_id: number }
    >({
      query: (data) => ({
        url: `knowledges/${data.bot_uuid}/files/${data.file_id}/download`,
        method: 'GET',
        responseHandler: (response) => response.blob()
      })
    }),
    getSyncStatus: builder.query<
      KnowledgeSyncStatusResponse,
      { bot_uuid: string }
    >({
      query: (data) => `knowledges/${data.bot_uuid}/sync-status`,
      providesTags: ['Knowledge']
    }),
    triggerSync: builder.mutation<void, { bot_uuid: string }>({
      query: (data) => ({ url: `knowledges/sync`, method: 'POST', body: data }),
      invalidatesTags: ['Knowledge']
    })
  })
})

export const {
  useLazyGetKnowledgeItemsQuery,
  useInsertKnowledgeItemMutation,
  useInsertKnowledgeItemsByCSVMutation,
  useUpdateKnowledgeItemMutation,
  useDeleteKnowledgeItemsMutation,
  useGetKnowledgeFilesQuery,
  useLazyGetKnowledgeFilesQuery,
  useInsertKnowledgeFilesMutation,
  useUpdateKnowledgeFileMutation,
  useDeleteKnowledgeFilesMutation,
  useLazyDownloadKnowledgeFileQuery,
  useGetSyncStatusQuery,
  useTriggerSyncMutation
} = knowledgeApi
