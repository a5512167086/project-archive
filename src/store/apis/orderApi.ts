import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

type OrderItem = {
  product_id: string
  variant_id: string
  quantity: number
}

export type OrderStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed'
export type OrderPaymentStatus = 'paid' | 'unpaid' | 'refunded'

export type GetOrdersResponse = {
  order_id: string
  object_id: number
  total_amount: number
  status: OrderStatus
  payment_method: string
  payment_status: OrderPaymentStatus
  shipping_method: string
  shipping_fee: number
  tracking_number: string
  recipient_name: string
  recipient_phone: string
  shipping_address: string
  created_at: string
  updated_at: string
  items: OrderItem[]
  notes: string
}

type GetOrdersRequest = {
  bot_uuid: string
}

export type UpdateOrderRequest = {
  bot_uuid: string
  order_id: string
  status: OrderStatus
  payment_status: OrderPaymentStatus
  tracking_number?: string
}

export const orderApi = createApi({
  reducerPath: 'orderApi',
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
    getOrders: builder.query<GetOrdersResponse[], GetOrdersRequest>({
      query: (data) => ({
        url: `orders/${data.bot_uuid}`,
        method: 'GET'
      })
    }),
    updateOrder: builder.mutation<void, UpdateOrderRequest>({
      query: (data) => ({
        url: `orders`,
        method: 'PATCH',
        body: {
          bot_uuid: data.bot_uuid,
          order_id: data.order_id,
          status: data.status,
          payment_status: data.payment_status,
          tracking_number: data.tracking_number
        }
      })
    })
  })
})

export const { useLazyGetOrdersQuery, useUpdateOrderMutation } = orderApi
