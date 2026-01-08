import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { botApi, BotInfo } from "@/store/apis/botApi";

interface BotState {
  info: BotInfo | null;
}

const initialState: BotState = {
  info: null,
};

export const botSlice = createSlice({
  name: "bot",
  initialState,
  reducers: {
    setBotInfo: (state, action: PayloadAction<BotInfo>) => {
      state.info = action.payload;
    },
    clearBotInfo: (state) => {
      state.info = null;
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(
      botApi.endpoints.getBotInfo.matchFulfilled,
      (state, action) => {
        state.info = action.payload;
      }
    );
  },
});

export const { setBotInfo, clearBotInfo } = botSlice.actions;

export default botSlice.reducer;
