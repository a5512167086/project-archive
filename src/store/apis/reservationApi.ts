import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

type GetReservationItemsRequest = {
  bot_uuid: string
}

type ReservationOption = {
  object_id: number
  option_id: string
  option_name: string
  option_description: string
  price: number
  is_required: boolean
  is_active: boolean
  type: string
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
  is_closed: boolean
  is_active: boolean
  note: string
  created_at: string
  updated_at: string
}

export type ReservationItemsResponse = {
  object_id: number
  class_id: number
  reservation_name: string
  reservation_description: string
  duration_minutes: number
  price: number
  options: ReservationOption[]
  schedules: ReservationSchedule[]
}

export type InsertReservationItemRequest = {
  bot_uuid: string
  reservation_name: string
  reservation_description: string
  duration_minutes: number
  price: number
  options?: {
    option_name: string
    option_description?: string
    price: number
    type: 'text' | 'select' | 'number'
    is_required?: boolean
    is_active?: boolean
  }[]
  default_schedules?: {
    schedule_type: 'weekly' | 'specific'
    weekday?: number
    schedule_date?: string
    start_time: string
    end_time: string
    capacity?: number
    is_closed?: boolean
    note?: string
    is_active?: boolean
  }[]
}

type DeleteReservationRequest = {
  bot_uuid: string
  delete_object_list: number[]
}

// PATCH 請求細節型別
export type ReservationItemDetailUpdate = {
  reservation_name?: string
  reservation_description?: string
  duration_minutes?: number
  price?: number
  is_active?: boolean
}

export type ReservationItemOptionUpdate = {
  option_id?: string // UUID
  option_name?: string
  option_description?: string
  price?: number
  type?: string
  is_required?: boolean
  is_active?: boolean
}

export type ReservationItemScheduleUpdate = {
  reservation_item_schedule_id?: string // UUID
  schedule_type?: string
  weekday?: number
  schedule_date?: string // ISO date string
  start_time?: string // ISO time string
  end_time?: string // ISO time string
  capacity?: number
  is_closed?: boolean
  note?: string
  is_active?: boolean
}

export type PatchReservationItemRequest = {
  bot_uuid: string
  object_id: number
  detail?: ReservationItemDetailUpdate
  options?: ReservationItemOptionUpdate[]
  schedules?: ReservationItemScheduleUpdate[]
}

export const reservationApi = createApi({
  reducerPath: 'reservationApi',
  baseQuery: fetchBaseQuery({ baseUrl: import.meta.env.VITE_BACKEND_URL }),
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
  usePatchReservationItemMutation
} = reservationApi
