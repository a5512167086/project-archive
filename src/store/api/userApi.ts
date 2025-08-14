import { baseApi } from "./baseApi";

export interface LoginRequest {
  line_id_token: string;
  bot_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

export const userApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    customerLogin: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: "/users/customer-login",
        method: "POST",
        body: credentials,
      }),
      invalidatesTags: ["User"],
    }),
  }),
});

export const { useCustomerLoginMutation } = userApi;