import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

type GetServicesRequest = {
  bot_uuid: string
}

// 新增：预约数据类型定义
export type ReservationData = {
  reservation_id: string
  service_id: string
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

// 更新預約的請求類型
export type UpdateReservationRequest = {
  bot_uuid: string
  reservation_id: string
  reservation_date?: string
  start_time?: string
  payment_method?: 'cash' | 'bank_transfer' | 'credit_card'
  payment_status?: 'paid' | 'unpaid' | 'refunded' | null
  status?: string
  note?: string
}

type ServiceOption = {
  option_id: string
  option_group_id: string
  option_name: string
  option_description: string
  price: number
  display_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

type ServiceOptionGroup = {
  option_group_id: string
  group_name: string
  group_description: string
  selection_type: 'single' | 'multiple'
  is_required: boolean
  display_order: number
  is_active: boolean
  options: ServiceOption[]
}

type ServiceSchedule = {
  service_schedule_id: string
  object_id: number
  schedule_type: string
  weekday: number
  schedule_date: string | null
  start_time: string
  end_time: string
  capacity: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type ServiceResponse = {
  service_id: string
  object_id: number
  class_id: number
  service_name: string
  service_description: string
  duration_minutes: number
  price: number
  is_active: boolean
  option_groups: ServiceOptionGroup[]
  schedules: ServiceSchedule[]
}

export type ServiceOptionCreate = {
  option_name: string
  option_description?: string | null
  price: number
  display_order: number
  is_active?: boolean
}

export type ServiceOptionGroupCreate = {
  group_name: string
  group_description?: string | null
  selection_type: 'single' | 'multiple'
  is_required: boolean
  display_order: number
  is_active: boolean
  options: ServiceOptionCreate[]
}

export type ServiceScheduleCreate = {
  schedule_type: 'weekly' | 'specific'
  weekday?: number | null // 0-6, required for weekly type, null for specific
  schedule_date?: string | null // ISO date string, required for specific type
  start_time: string // Time format
  end_time: string // Time format
  capacity?: number
  is_active?: boolean
}

export type InsertServiceRequest = {
  bot_uuid: string
  service_name: string
  service_description: string
  duration_minutes: number
  price: number
  option_groups: ServiceOptionGroupCreate[]
  default_schedules: ServiceScheduleCreate[]
}

type DeleteServicesRequest = {
  bot_uuid: string
  delete_service_list: string[]
}

// PATCH 請求細節型別 - 匹配後端 Pydantic schema
export type ServiceDetailUpdate = {
  service_name?: string
  service_description?: string
  duration_minutes?: number
  price?: number
  is_active?: boolean
}

export type ServiceOptionGroupUpdate = {
  option_group_id?: string // UUID - 更新現有組時必須提供
  group_name?: string
  group_description?: string | null
  selection_type?: 'single' | 'multiple'
  is_required?: boolean
  display_order?: number
  is_active?: boolean
  options?: ServiceOptionUpdate[]
}

export type ServiceOptionUpdate = {
  option_id?: string // UUID - 更新現有選項時必須提供
  option_name?: string
  option_description?: string | null
  price?: number
  display_order?: number
  is_active?: boolean
}

export type ServiceScheduleUpdate = {
  reservation_service_schedule_id?: string // UUID - 更新現有排程時必須提供
  schedule_type?: string
  weekday?: number
  schedule_date?: string // ISO date string for specific type
  start_time?: string // Time format from backend
  end_time?: string // Time format from backend
  capacity?: number
  is_active?: boolean
}

export type PatchServiceRequest = {
  bot_uuid: string
  service_id: string
  detail?: ServiceDetailUpdate
  option_groups?: ServiceOptionGroupUpdate[]
  schedules?: ServiceScheduleUpdate[]
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
    getServices: builder.query<ServiceResponse[], GetServicesRequest>({
      query: (data) => ({
        url: `services/${data.bot_uuid}`,
        method: 'GET'
      })
    }),
    getReservations: builder.query<ReservationData[], GetReservationsRequest>({
      query: (data) => ({
        url: `reservations/${data.bot_uuid}`,
        method: 'GET'
      })
    }),
    updateReservation: builder.mutation<void, UpdateReservationRequest>({
      query: (data) => ({
        url: 'reservations',
        method: 'PATCH',
        body: data
      })
    }),
    insertService: builder.mutation<void, InsertServiceRequest>({
      query: (data) => ({
        url: `services`,
        method: 'POST',
        body: data
      })
    }),
    deleteServices: builder.mutation<void, DeleteServicesRequest>({
      query: (data) => ({
        url: 'services',
        method: 'DELETE',
        body: data
      })
    }),
    patchService: builder.mutation<void, PatchServiceRequest>({
      query: (body) => ({
        url: 'services',
        method: 'PATCH',
        body
      })
    })
  })
})

export const {
  useLazyGetServicesQuery,
  useInsertServiceMutation,
  useDeleteServicesMutation,
  usePatchServiceMutation,
  useGetReservationsQuery,
  useLazyGetReservationsQuery,
  useUpdateReservationMutation
} = reservationApi
