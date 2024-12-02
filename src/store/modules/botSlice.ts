import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CustomError } from '@/configs/type'
import { clearUserToken } from '@/utils/helper'
import { botApi, BotsResponse } from '../apis/botApi'

interface BotState {
  botList: BotsResponse[]
  currentBot: BotsResponse | null
  errorCode: string
  errorMessage: string
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
}

const initialState: BotState = {
  botList: [],
  currentBot: null,
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
    setCurrentBot: (state, action) => {
      state.currentBot = action.payload
    },
    clearCurrentBot: (state) => {
      state.currentBot = null
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
        clearUserToken()
        state.status = 'failed'
        state.errorCode = action.error.code!
        state.errorMessage = action.error.message!
      })
  }
})

export const {
  initBot,
  setBotError,
  setCurrentBot,
  clearCurrentBot,
  clearBotError
} = botSlice.actions

export default botSlice.reducer
