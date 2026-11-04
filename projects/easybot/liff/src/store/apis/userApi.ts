import { baseApi } from "./baseApi";
import { OrderItem } from "./ecommApi";
import { UserReservationOptionGroup } from "./reservationApi";

export interface LoginRequest {
  line_id_token: string;
  bot_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

export interface UserReservation {
  reservation_id: string;
  service_id: string;
  service_name: string;
  price: number;
  notes: string;
  reservation_date: string; // YYYY-MM-DD 格式
  start_time: string; // ISO 8601 格式
  end_time: string; // ISO 8601 格式
  status: string;
  payment_method: string;
  payment_status: string;
  created_at: string; // ISO 8601 格式
  selected_option_groups: UserReservationOptionGroup[];
}

export type UserReservationsResponse = UserReservation[];

export interface UserOrder {
  order_id: string;
  object_id: number;
  total_amount: number;
  status: string;
  payment_method: string;
  payment_status: string;
  shipping_method: string;
  shipping_fee: number;
  tracking_number: string;
  recipient_name: string;
  recipient_phone: string;
  shipping_address: string;
  items: OrderItem[];
  notes: string;
  created_at: string;
  updated_at: string;
}

export type UserOrdersResponse = UserOrder[];

export type TokenRefreshRequest = {
  refresh_token: string;
};

export type TokenRefreshResponse = {
  access_token: string;
  refresh_token: string;
};

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
    refreshToken: builder.mutation<TokenRefreshResponse, TokenRefreshRequest>({
      query: (data) => ({
        url: "/users/token-refresh",
        method: "POST",
        body: data,
      }),
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
    getUserOrders: builder.query<UserOrdersResponse, string>({
      query: (botUuid) => `/orders/user/${botUuid}`,
      providesTags: (result, error, botUuid) => [
        { type: "UserOrder", id: `user-${botUuid}` },
        ...(result || []).map((order) => ({
          type: "UserOrder" as const,
          id: order.order_id,
        })),
      ],
    }),
  }),
});

export const {
  useCustomerLoginMutation,
  useRefreshTokenMutation,
  useGetUserReservationsQuery,
  useGetUserOrdersQuery,
} = userApi;
