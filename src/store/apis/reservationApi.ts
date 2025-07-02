import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

type GetReservationItemsRequest = {
  bot_uuid: string
}

// 新增：预约数据类型定义
export type ReservationData = {
  reservation_id: string
  reservation_item_id: string
  price: number
  service_name: string
  notes: string | null
  reservation_date: string
  start_time: string
  end_time: string
  status: string
  payment_method: string
  payment_status: string | null
  created_at: string
  selected_option_groups: {
    option_group_id: string
    group_name: string
    selected_options: {
      option_id: string
      option_name: string
    }[]
  }[]
}

type GetReservationsRequest = {
  bot_uuid: string
}

type ReservationOption = {
  object_id: number
  option_id: string
  option_name: string
  option_description: string
  price: number
  display_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

type ReservationOptionGroup = {
  object_id: number
  option_group_id: string
  group_name: string
  group_description: string
  selection_type: 'single' | 'multiple'
  is_required: boolean
  display_order: number
  is_active: boolean
  options: ReservationOption[]
  created_at: string
  updated_at: string
}

type ReservationSchedule = {
  object_id: number
  reservation_item_schedule_id: string
  schedule_type: string
  schedule_date: string | null
  weekday: number
  start_time: string
  end_time: string
  capacity: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type ReservationItemsResponse = {
  reservation_item_id: string
  object_id: number
  class_id: number
  reservation_name: string
  reservation_description: string
  duration_minutes: number
  price: number
  option_groups: ReservationOptionGroup[]
  schedules: ReservationSchedule[]
}

export type ReservationItemOptionCreate = {
  option_name: string
  option_description?: string | null
  price: number
  display_order: number
  is_active?: boolean
}

export type ReservationOptionGroupCreate = {
  group_name: string
  group_description?: string | null
  selection_type: 'single' | 'multiple' // Based on SelectionType enum
  is_required: boolean
  display_order: number
  is_active: boolean
  options: ReservationItemOptionCreate[]
}

export type ReservationItemScheduleCreate = {
  schedule_type: 'weekly' | 'specific'
  weekday?: number | null // 0-6, required for weekly type, null for specific
  schedule_date?: string | null // ISO date string, required for specific type
  start_time: string // Time format
  end_time: string // Time format
  capacity?: number
  is_active?: boolean
}

export type InsertReservationItemRequest = {
  bot_uuid: string
  reservation_name: string
  reservation_description: string
  duration_minutes: number
  price: number
  option_groups: ReservationOptionGroupCreate[]
  default_schedules: ReservationItemScheduleCreate[]
}

type DeleteReservationRequest = {
  bot_uuid: string
  delete_reservation_item_list: string[]
}

// PATCH 請求細節型別 - 匹配後端 Pydantic schema
export type ReservationItemDetailUpdate = {
  reservation_name?: string
  reservation_description?: string
  duration_minutes?: number
  price?: number
  is_active?: boolean
}

export type ReservationItemOptionGroupUpdate = {
  option_group_id?: string // UUID - 更新現有組時必須提供
  group_name?: string
  group_description?: string | null
  selection_type?: 'single' | 'multiple'
  is_required?: boolean
  display_order?: number
  is_active?: boolean
  options?: ReservationItemOptionUpdate[]
}

export type ReservationItemOptionUpdate = {
  option_id?: string // UUID - 更新現有選項時必須提供
  option_name?: string
  option_description?: string | null
  price?: number
  display_order?: number
  is_active?: boolean
}

export type ReservationItemScheduleUpdate = {
  reservation_item_schedule_id?: string // UUID - 更新現有排程時必須提供
  schedule_type?: string
  weekday?: number
  schedule_date?: string // ISO date string for specific type
  start_time?: string // Time format from backend
  end_time?: string // Time format from backend
  capacity?: number
  is_active?: boolean
}

export type PatchReservationItemRequest = {
  bot_uuid: string
  reservation_item_id: string
  detail?: ReservationItemDetailUpdate
  option_groups?: ReservationItemOptionGroupUpdate[]
  schedules?: ReservationItemScheduleUpdate[]
}

export const reservationApi = createApi({
  reducerPath: 'reservationApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_BACKEND_URL,
    prepareHeaders: (headers) => {
      if (!headers.has('Authorization')) {
        const token =
          localStorage.getItem('access_token') ||
          sessionStorage.getItem('access_token')
        if (token) {
          headers.set('Authorization', `Bearer ${token}`)
        }
      }
      return headers
    }
  }),
  endpoints: (builder) => ({
    getServices: builder.query<
      ReservationItemsResponse[],
      GetReservationItemsRequest
    >({
      query: (data) => ({
        url: `reservations/items/${data.bot_uuid}`,
        method: 'GET'
      })
    }),
    getReservations: builder.query<
      ReservationData[],
      GetReservationsRequest
    >({
      query: (data) => ({
        url: `reservations/${data.bot_uuid}`,
        method: 'GET'
      })
    }),
    insertService: builder.mutation<void, InsertReservationItemRequest>({
      query: (data) => ({
        url: `reservations/items`,
        method: 'POST',
        body: data
      })
    }),
    deleteReservationItems: builder.mutation<void, DeleteReservationRequest>({
      query: (data) => ({
        url: 'reservations/items',
        method: 'DELETE',
        body: data
      })
    }),
    patchReservationItem: builder.mutation<void, PatchReservationItemRequest>({
      query: (body) => ({
        url: '/reservations/items',
        method: 'PATCH',
        body
      })
    })
  })
})

export const {
  useLazyGetServicesQuery,
  useInsertServiceMutation,
  useDeleteReservationItemsMutation,
  usePatchReservationItemMutation,
  useGetReservationsQuery,
  useLazyGetReservationsQuery
} = reservationApi
