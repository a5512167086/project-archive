import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

type GetReservationItemsRequest = {
  bot_class_id: number
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

export const reservationApi = createApi({
  reducerPath: 'reservationApi',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_BACKEND_URL
  }),
  endpoints: (builder) => ({
    getServices: builder.query<
      ReservationItemsResponse[],
      GetReservationItemsRequest
    >({
      query: (data) => ({
        url: `reservations/items/${data.bot_class_id}`,
        method: 'GET'
      })
    })
  })
})

export const { useLazyGetServicesQuery } = reservationApi
