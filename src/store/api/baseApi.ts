import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

// 基礎查詢配置
export const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_BASE_URL,
  prepareHeaders: (headers, { endpoint }) => {
    // 優先使用 access_token，如果沒有則使用 token
    const accessToken = localStorage.getItem("access_token");
    const token = localStorage.getItem("token");
    const authToken = accessToken || token;

    console.log(`📡 API 請求: ${endpoint}`, {
      hasAccessToken: !!accessToken,
      hasToken: !!token,
      tokenLength: authToken ? authToken.length : 0,
    });

    if (authToken) {
      headers.set("authorization", `Bearer ${authToken}`);
    }
    headers.set("Content-Type", "application/json");
    return headers;
  },
});

// 基礎 API 配置
export const baseApi = createApi({
  reducerPath: "api",
  baseQuery,
  tagTypes: ["Reservation", "ReservationItem", "User", "UserReservation"],
  endpoints: () => ({}),
});
