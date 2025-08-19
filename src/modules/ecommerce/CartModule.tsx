import { ShoppingCart } from "lucide-react";
import type { AppModule } from "@/types/module";
import { CartPage } from "@/pages/CartPage";

export const cartModule: AppModule = {
  config: {
    id: "cart",
    name: "購物車",
    icon: ShoppingCart,
    color: "blue",
    description: "查看您的購物車",
  },
  component: {
    id: "cart",
    render: () => <CartPage />,
  },
};
