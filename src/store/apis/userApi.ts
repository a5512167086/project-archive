import { baseApi } from "./baseApi";
import { UserReservationsResponse } from "./reservationApi";

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
    getUserReservations: builder.query<UserReservationsResponse, string>({
      query: (botUuid) => `/reservations/user/${botUuid}`,
      providesTags: (result, error, botUuid) => [
        { type: "UserReservation", id: `user-${botUuid}` },
        ...(result || []).map((reservation) => ({
          type: "UserReservation" as const,
          id: reservation.reservation_id,
        })),
      ],
    }),
  }),
});

export const { useCustomerLoginMutation, useGetUserReservationsQuery } = userApi;
