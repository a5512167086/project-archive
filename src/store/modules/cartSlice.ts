import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface CartItem {
  itemId: string;
  productId: string;
  variantId?: string | null;
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
        productId: string;
        variantId?: string | null;
        quantity: number;
      }>
    ) => {
      const { productId, quantity, variantId } = action.payload;

      const itemId = variantId ? `${productId}-${variantId}` : productId;

      const existingItem = state.items.find((item) => item.itemId === itemId);

      if (existingItem) {
        existingItem.quantity += quantity;
      } else {
        state.items.push({
          itemId: itemId,
          productId: productId,
          quantity,
          variantId: variantId || null,
        });
      }
    },
    removeFromCart: (state, action: PayloadAction<{ itemId: string }>) => {
      state.items = state.items.filter(
        (item) => item.itemId !== action.payload.itemId
      );
    },
    updateQuantity: (
      state,
      action: PayloadAction<{
        itemId: string;
        quantity: number;
      }>
    ) => {
      const { itemId, quantity } = action.payload;
      const item = state.items.find((item) => item.itemId === itemId);
      if (item) {
        if (quantity > 0) {
          item.quantity = quantity;
        } else {
          state.items = state.items.filter((i) => i.itemId !== itemId);
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
