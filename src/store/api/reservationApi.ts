import { baseApi } from "./baseApi";

export interface Reservation {
  id: string;
  title: string;
  date: string;
  description: string;
  status: string;
  price: number;
  statusColor: "green" | "blue" | "orange" | "red";
}

export interface ReservationsResponse {
  reservations: Reservation[];
  total: number;
}

export interface ReservationFilters {
  status?: string;
  page?: number;
  limit?: number;
}

export interface CreateReservationRequest {
  title: string;
  date: string;
  description?: string;
  price: number;
}

export interface BotInfo {
  id: string;
  name: string;
  liff_id: string;
  description?: string;
}

export interface LoginRequest {
  line_id_token: string;
  bot_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

// 預約服務項目相關類型 - 基於實際 API 回應結構
export interface ReservationItemOption {
  option_id: string;
  option_group_id: string;
  option_name: string;
  option_description: string;
  price: number;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReservationItemOptionGroup {
  option_group_id: string;
  group_name: string;
  group_description: string;
  selection_type: "single" | "multiple";
  is_required: boolean;
  display_order: number;
  is_active: boolean;
  options: ReservationItemOption[];
}

export interface ReservationItemSchedule {
  reservation_item_schedule_id: string;
  object_id: number;
  schedule_type: "weekly" | "daily";
  weekday: number; // 1=Monday, 2=Tuesday, etc.
  schedule_date: string | null;
  start_time: string; // HH:mm:ss format
  end_time: string; // HH:mm:ss format
  capacity: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReservationItem {
  reservation_item_id: string;
  object_id: number;
  class_id: number;
  reservation_name: string;
  reservation_description: string;
  duration_minutes: number;
  price: number;
  option_groups: ReservationItemOptionGroup[];
  schedules: ReservationItemSchedule[];
}

// API 回應是直接的陣列，不是包在物件裡
export type ReservationItemsResponse = ReservationItem[];

// 可預約時間相關類型
export interface AvailableTime {
  start_time: string; // HH:mm:ss 格式
  end_time: string; // HH:mm:ss 格式
  available_capacity: number;
}

export interface AvailableDate {
  date: string; // YYYY-MM-DD 格式
  times: AvailableTime[];
}

export type AvailableTimesResponse = AvailableDate[];

// 創建預約相關類型
export interface CreateReservationOptionValue {
  option_id: string;
  value: string;
}

export interface CreateReservationPayload {
  bot_uuid: string;
  reservation_item_id: string;
  reservation_date: string; // YYYY-MM-DD 格式
  start_time: string; // ISO 8601 格式或 HH:mm:ss 格式
  payment_method: "cash" | "bank_transfer";
  option_values: CreateReservationOptionValue[];
  notes?: string;
}

export interface CreateReservationResponse {
  id: string;
  status: string;
  message: string;
}

// 用戶預約記錄相關類型
export interface UserReservationSelectedOption {
  option_id: string;
  option_name: string;
  price?: number; // 選項價格
}

export interface UserReservationOptionGroup {
  option_group_id: string;
  group_name: string;
  selected_options: UserReservationSelectedOption[];
}

export interface UserReservation {
  reservation_id: string;
  reservation_item_id: string;
  service_name: string;
  reservation_date: string; // YYYY-MM-DD 格式
  start_time: string; // HH:mm:ss 格式
  end_time: string; // HH:mm:ss 格式
  status: "pending" | "confirmed" | "cancelled" | "completed";
  payment_method: "cash" | "credit_card" | "bank_transfer";
  payment_status: "paid" | "unpaid" | "pending" | null;
  created_at: string; // ISO 8601 格式
  selected_option_groups: UserReservationOptionGroup[];
  price: number; // 預約總價格
  notes?: string; // 備註
}

export type UserReservationsResponse = UserReservation[];

export const reservationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // 預約相關 endpoints
    getReservations: builder.query<ReservationsResponse, ReservationFilters>({
      query: (filters = {}) => {
        const params = new URLSearchParams();
        if (filters.status && filters.status !== "all") {
          params.append("status", filters.status);
        }
        if (filters.page) {
          params.append("page", filters.page.toString());
        }
        if (filters.limit) {
          params.append("limit", filters.limit.toString());
        }
        return `/reservations?${params.toString()}`;
      },
      providesTags: ["Reservation"],
    }),
    getReservationById: builder.query<Reservation, string>({
      query: (id) => `/reservations/${id}`,
      providesTags: (result, error, id) => [{ type: "Reservation", id }],
    }),
    createReservation: builder.mutation<Reservation, CreateReservationRequest>({
      query: (reservation) => ({
        url: "/reservations",
        method: "POST",
        body: reservation,
      }),
      invalidatesTags: ["Reservation"],
    }),
    updateReservationStatus: builder.mutation<
      Reservation,
      { id: string; status: string }
    >({
      query: ({ id, status }) => ({
        url: `/reservations/${id}/status`,
        method: "PUT",
        body: { status },
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: "Reservation", id },
        "Reservation",
      ],
    }),
    cancelReservation: builder.mutation<void, string>({
      query: (id) => ({
        url: `/reservations/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, id) => [
        { type: "Reservation", id },
        "Reservation",
      ],
    }),
    createNewReservation: builder.mutation<
      CreateReservationResponse,
      CreateReservationPayload
    >({
      query: (reservation) => ({
        url: "/reservations",
        method: "POST",
        body: reservation,
      }),
      invalidatesTags: (result, error, { bot_uuid }) => [
        "Reservation",
        { type: "UserReservation", id: `user-${bot_uuid}` },
      ],
    }),

    // 預約服務項目 endpoints
    getReservationItems: builder.query<ReservationItemsResponse, string>({
      query: (botUuid) => `/reservations/items/${botUuid}`,
      providesTags: (result, error, botUuid) => [
        { type: "ReservationItem", id: `items-${botUuid}` },
      ],
    }),
    getAvailableTimes: builder.query<AvailableTimesResponse, string>({
      query: (reservationItemId) =>
        `/reservations/items/${reservationItemId}/available-times`,
      providesTags: (result, error, reservationItemId) => [
        { type: "ReservationItem", id: `times-${reservationItemId}` },
      ],
    }),

    // 用戶預約記錄 endpoints
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

    // LIFF 相關 endpoints (保留這些因為登入還是需要的)
    getBotInfo: builder.query<BotInfo, string>({
      query: (botUUID) => `/bots/${botUUID}`,
      providesTags: ["User"],
    }),
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

export const {
  useGetReservationsQuery,
  useGetReservationByIdQuery,
  useCreateReservationMutation,
  useUpdateReservationStatusMutation,
  useCancelReservationMutation,
  useCreateNewReservationMutation,
  useGetReservationItemsQuery,
  useGetAvailableTimesQuery,
  useGetUserReservationsQuery,
  useGetBotInfoQuery,
  useCustomerLoginMutation,
} = reservationApi;
