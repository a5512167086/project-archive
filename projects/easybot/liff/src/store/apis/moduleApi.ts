import { baseApi } from "./baseApi";

export enum ModuleType {
  Ecomm = "Ecomm",
  Reservation = "Reservation",
  FAQ = "FAQ",
}

export interface ModuleSetting {
  module_id: string;
  class_id: number;
  object_id: number;
  chinese_name: ModuleType;
  is_enabled: boolean;
  version: string;
  description: string | null;
}

export const moduleApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getModuleSettings: builder.query<ModuleSetting[], string>({
      query: (bot_uuid) => `/modules/${bot_uuid}`,
      providesTags: ["Module"],
    }),
  }),
});

export const { useGetModuleSettingsQuery } = moduleApi;
