import { createSlice } from "@reduxjs/toolkit";
import { moduleApi, ModuleSetting } from "@/store/apis/moduleApi";

interface ModuleState {
  settings: ModuleSetting[];
}

const initialState: ModuleState = {
  settings: [],
};

export const moduleSlice = createSlice({
  name: "module",
  initialState,
  reducers: {
    // 登出或切換 Bot 時清除資料
    clearModules: (state) => {
      state.settings = [];
    },
  },
  extraReducers: (builder) => {
    // 自動監聽 getModuleSettings 成功後的資料
    builder.addMatcher(
      moduleApi.endpoints.getModuleSettings.matchFulfilled,
      (state, action) => {
        state.settings = action.payload;
      }
    );
  },
});

export const { clearModules } = moduleSlice.actions;

export default moduleSlice.reducer;
