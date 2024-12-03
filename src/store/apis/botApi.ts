import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export type BotsResponse = {
  class_id: number
  object_id: number
  bot_name: string
  channel_id: string
  owner_id: string
}

export type CreateBotRequest = {
  bot_name: string
  bot_channel_id: string
  bot_channel_access_token: string
  bot_channel_secret: string
}

export type CreateBotResponse = {
  webhook_url: string
}

export type DeleteBotRequest = {
  bot_class_id: number
}

export type UpdateBotRequest = {
  bot_class_id: number
  bot_name?: string
  channel_id?: string
  channel_access_token?: string
  channel_secret?: string
}
export const botApi = createApi({
  reducerPath: 'botApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_BOT_BACKEND_URL,
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
    getBots: builder.query<BotsResponse[], void>({
      query: () => ({
        url: 'bots',
        method: 'GET'
      })
    }),
    createBot: builder.mutation<CreateBotResponse, CreateBotRequest>({
      query: (bot) => ({
        url: 'bot',
        method: 'POST',
        body: bot
      })
    }),
    updateBot: builder.mutation<void, UpdateBotRequest>({
      query: (bot) => ({
        url: `bot/${bot.bot_class_id}`,
        method: 'PATCH',
        body: bot
      })
    }),
    deleteBot: builder.mutation<void, DeleteBotRequest>({
      query: (bot) => ({
        url: `bot/${bot.bot_class_id}`,
        method: 'DELETE'
      })
    })
  })
})

export const {
  useLazyGetBotsQuery,
  useCreateBotMutation,
  useUpdateBotMutation,
  useDeleteBotMutation
} = botApi
