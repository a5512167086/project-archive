import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Product, ProductVariant } from "../apis/ecommApi";

export interface CartItem {
  id: string; // combination of product_id and variant_id
  product: Product;
  variant?: ProductVariant;
  quantity: number;
}

interface CartState {
  items: CartItem[];
}

const initialState: CartState = {
  items: [],
};

const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {
    addToCart: (
      state,
      action: PayloadAction<{
        product: Product;
        quantity: number;
        variantId?: string | null;
      }>
    ) => {
      const { product, quantity, variantId } = action.payload;
      const variant = variantId
        ? product.variants.find((v) => v.variant_id === variantId)
        : undefined;

      const cartItemId = variant
        ? `${product.product_id}-${variant.variant_id}`
        : product.product_id;

      const existingItem = state.items.find((item) => item.id === cartItemId);

      if (existingItem) {
        existingItem.quantity += quantity;
      } else {
        state.items.push({
          id: cartItemId,
          product,
          quantity,
          variant,
        });
      }
    },
    removeFromCart: (state, action: PayloadAction<{ cartItemId: string }>) => {
      state.items = state.items.filter(
        (item) => item.id !== action.payload.cartItemId
      );
    },
    updateQuantity: (
      state,
      action: PayloadAction<{
        cartItemId: string;
        quantity: number;
      }>
    ) => {
      const { cartItemId, quantity } = action.payload;
      const item = state.items.find((item) => item.id === cartItemId);
      if (item) {
        if (quantity > 0) {
          item.quantity = quantity;
        } else {
          state.items = state.items.filter((i) => i.id !== cartItemId);
        }
      }
    },
    clearCart: (state) => {
      state.items = [];
    },
  },
});

export const { addToCart, removeFromCart, updateQuantity, clearCart } =
  cartSlice.actions;

export default cartSlice.reducer;