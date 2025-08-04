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

export interface Product {
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
  images: unknown[];
  variants: unknown[];
}

export type ProductsResponse = Product[];

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
  }),
});

export const { useGetBrandsQuery, useGetCategoriesQuery, useGetProductsQuery } = ecommApi;
