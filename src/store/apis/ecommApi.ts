import { baseApi } from "./baseApi";

export interface Brand {
  class_id: number;
  object_id: number;
  brand_name: string;
  brand_description: string;
}

export type BrandsResponse = Brand[];

export interface Category {
  parent_class_id: number | null;
  class_id: number;
  category_name: string;
  category_description: string;
  children: Category[];
}

export type CategoriesResponse = Category[];

export type ProductImage = {
  image_id: number;
  filename: string;
  image_url: string;
  is_primary: boolean;
};
export type ProductVariant = {
  variant_id: string;
  object_id: number;
  variant_name: string;
  sku_code: string;
  price: number;
  stock: number;
  created_at: string;
  updated_at: string;
};

export type Product = {
  product_id: string;
  object_id: number;
  product_name: string;
  product_description: string;
  brand_id: number;
  category_id: number;
  sku_code: string;
  price: number;
  stock: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  images: ProductImage[];
  variants: ProductVariant[];
};

export type ProductsResponse = Product[];

export type OrderItem = {
  product_id: string;
  variant_id: string;
  quantity: number;
};

export type CreateOrderRequest = {
  bot_uuid: string;
  payment_method: "cash" | "bank_transfer";
  shipping_method: "home_delivery" | "store_pickup";
  recipient_name: string;
  recipient_phone: string;
  shipping_address?: string;
  notes?: string;
  items: OrderItem[];
};

export const ecommApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getBrands: builder.query<BrandsResponse, string>({
      query: (botUuid) => `/brands/${botUuid}`,
      providesTags: (result, error, botUuid) => [
        { type: "Brand", id: `brands-${botUuid}` },
      ],
    }),
    getCategories: builder.query<CategoriesResponse, string>({
      query: (botUuid) => `/categories/${botUuid}`,
      providesTags: (result, error, botUuid) => [
        { type: "Category", id: `categories-${botUuid}` },
      ],
    }),
    getProducts: builder.query<ProductsResponse, string>({
      query: (botUuid) => `/products/${botUuid}`,
      providesTags: (result, error, botUuid) => [
        { type: "Product", id: `products-${botUuid}` },
      ],
    }),
    createOrder: builder.mutation<void, CreateOrderRequest>({
      query: (order) => ({
        url: "/orders",
        method: "POST",
        body: order,
      }),
    }),
  }),
});

export const {
  useGetBrandsQuery,
  useGetCategoriesQuery,
  useGetProductsQuery,
  useCreateOrderMutation,
} = ecommApi;
