import { baseApi } from './baseApi'

// Types 保持不變
export type BotsResponse = {
  bot_detail_id: string
  class_id: number
  object_id: number
  chinese_name: string
  channel_id: string
  owner_id: string
}

export type CreateBotRequest = {
  bot_name: string
  bot_channel_id: string
  bot_channel_access_token: string
  bot_channel_secret: string
  bot_login_channel_id: string
  bot_login_channel_secret: string
}

export type CreateBotResponse = {
  webhook_url: string
}

export type DeleteBotRequest = {
  bot_uuid: string
}

export type UpdateBotRequest = {
  bot_uuid: string
  bot_name?: string
  channel_id?: string
  channel_access_token?: string
  channel_secret?: string
  login_channel_id?: string
  login_channel_secret?: string
}

// 2. 改用 baseApi.injectEndpoints
export const botApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getBots: builder.query<BotsResponse[], void>({
      query: () => ({
        url: 'bots',
        method: 'GET'
      }),
      // 建議加入 Tag，這樣新增/刪除後列表會自動重整
      providesTags: ['Bot']
    }),
    createBot: builder.mutation<CreateBotResponse, CreateBotRequest>({
      query: (bot) => ({
        url: 'bots',
        method: 'POST',
        body: bot
      }),
      // 新增成功後，讓 getBots 自動重抓
      invalidatesTags: ['Bot']
    }),
    updateBot: builder.mutation<void, UpdateBotRequest>({
      query: (bot) => ({
        url: `bots/${bot.bot_uuid}`,
        method: 'PATCH',
        body: bot
      }),
      invalidatesTags: ['Bot']
    }),
    deleteBot: builder.mutation<void, DeleteBotRequest>({
      query: (bot) => ({
        url: `bots/${bot.bot_uuid}`,
        method: 'DELETE'
      }),
      invalidatesTags: ['Bot']
    })
  })
})

// 3. Export Hooks 保持不變
export const {
  useLazyGetBotsQuery,
  useCreateBotMutation,
  useUpdateBotMutation,
  useDeleteBotMutation
} = botApi
