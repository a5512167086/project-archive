import { baseApi } from "./baseApi";

export interface BotInfo {
  id: string;
  name: string;
  liff_id: string;
  description?: string;
}

export const botApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getBotInfo: builder.query<BotInfo, string>({
      query: (botUUID) => `/bots/${botUUID}`,
      providesTags: ["Bot"],
    }),
  }),
});

export const { useGetBotInfoQuery } = botApi;