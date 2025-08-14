import { createSlice } from "@reduxjs/toolkit";
import {
  ecommApi,
  ProductsResponse,
  BrandsResponse,
  CategoriesResponse,
} from "../apis/ecommApi";

interface ProductState {
  products: ProductsResponse;
  brands: BrandsResponse;
  categories: CategoriesResponse;
  errorCode: string;
  errorMessage: string;
  status: "idle" | "loading" | "succeeded" | "failed";
}

const initialState: ProductState = {
  products: [],
  brands: [],
  categories: [],
  errorCode: "",
  errorMessage: "",
  status: "idle",
};

export const ecommSlice = createSlice({
  name: "ecomm",
  initialState,
  reducers: {
    clearProductError: (state) => {
      state.errorCode = "";
      state.errorMessage = "";
      state.status = "idle";
    },
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(ecommApi.endpoints.getBrands.matchPending, (state) => {
        state.status = "loading";
      })
      .addMatcher(
        ecommApi.endpoints.getBrands.matchFulfilled,
        (state, action) => {
          state.status = "succeeded";
          state.brands = action.payload;
        }
      )
      .addMatcher(ecommApi.endpoints.getCategories.matchPending, (state) => {
        state.status = "loading";
      })
      .addMatcher(
        ecommApi.endpoints.getCategories.matchFulfilled,
        (state, action) => {
          state.status = "succeeded";
          state.categories = action.payload;
        }
      )
      .addMatcher(ecommApi.endpoints.getProducts.matchPending, (state) => {
        state.status = "loading";
      })
      .addMatcher(
        ecommApi.endpoints.getProducts.matchFulfilled,
        (state, action) => {
          state.status = "succeeded";
          state.products = action.payload;
        }
      );
  },
});

export const { clearProductError } = ecommSlice.actions;

export default ecommSlice.reducer;
