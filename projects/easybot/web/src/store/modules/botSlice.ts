import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { botApi, BotsResponse } from '../apis/botApi'

interface BotState {
  botList: BotsResponse[]
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: BotState = {
  botList: [],
  errorCode: '',
  errorMessage: '',
  status: 'idle'
}

export const botSlice = createSlice({
  name: 'bot',
  initialState,
  reducers: {
    initBot: (state) => {
      state.botList = []
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    },
    setBotError: (state, action: PayloadAction<CustomError>) => {
      state.errorCode = action.payload.error_code
      state.errorMessage = action.payload.error_message
      state.status = 'failed'
    },
    clearBotError: (state) => {
      state.errorCode = ''
      state.errorMessage = ''
      state.status = 'idle'
    }
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(botApi.endpoints.getBots.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(botApi.endpoints.getBots.matchFulfilled, (state, action) => {
        state.status = 'succeeded'
        state.botList = action.payload
      })
      .addMatcher(botApi.endpoints.getBots.matchRejected, (state, action) => {
        const error = action.payload!.data as CustomError
        state.status = 'failed'
        state.errorCode = error['error_code']
        state.errorMessage = error['error_message']
      })
      .addMatcher(botApi.endpoints.createBot.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(botApi.endpoints.createBot.matchFulfilled, (state) => {
        state.status = 'succeeded'
      })
      .addMatcher(botApi.endpoints.createBot.matchRejected, (state, action) => {
        const error = action.payload!.data as CustomError
        state.status = 'failed'
        state.errorCode = error['error_code']
        state.errorMessage = error['error_message']
      })
      .addMatcher(botApi.endpoints.deleteBot.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(botApi.endpoints.deleteBot.matchFulfilled, (state) => {
        state.status = 'succeeded'
      })
      .addMatcher(botApi.endpoints.deleteBot.matchRejected, (state, action) => {
        const error = action.payload!.data as CustomError
        state.status = 'failed'
        state.errorCode = error['error_code']
        state.errorMessage = error['error_message']
      })
      .addMatcher(botApi.endpoints.updateBot.matchPending, (state) => {
        state.status = 'loading'
      })
      .addMatcher(botApi.endpoints.updateBot.matchFulfilled, (state) => {
        state.status = 'succeeded'
      })
      .addMatcher(botApi.endpoints.updateBot.matchRejected, (state, action) => {
        const error = action.payload!.data as CustomError
        state.status = 'failed'
        state.errorCode = error['error_code']
        state.errorMessage = error['error_message']
      })
  }
})

export const { initBot, setBotError, clearBotError } = botSlice.actions

export default botSlice.reducer
