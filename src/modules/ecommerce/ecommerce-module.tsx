import { ShoppingBag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "../../components/SearchInput";
import { ProductCard } from "../../components/ProductCard";
import { FeaturedItem } from "../../components/FeaturedItem";
import type { AppModule } from "../../types/module";

const products = [
  {
    id: "1",
    name: "精華液套組",
    price: 899,
    rating: 4.5,
    image: "/placeholder.svg?height=120&width=120",
  },
  {
    id: "2",
    name: "維他命C錠",
    price: 450,
    rating: 4.8,
    image: "/placeholder.svg?height=120&width=120",
  },
];

function EcommerceContent() {
  return (
    <div className="space-y-4">
      <SearchInput placeholder="搜尋商品..." />

      <div className="flex space-x-2 overflow-x-auto pb-2">
        <Badge variant="secondary" className="whitespace-nowrap">
          全部
        </Badge>
        <Badge variant="outline" className="whitespace-nowrap">
          美妝保養
        </Badge>
        <Badge variant="outline" className="whitespace-nowrap">
          健康食品
        </Badge>
        <Badge variant="outline" className="whitespace-nowrap">
          運動用品
        </Badge>
        <Badge variant="outline" className="whitespace-nowrap">
          居家用品
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            id={product.id}
            name={product.name}
            price={product.price}
            rating={product.rating}
            image={product.image}
            onAddToCart={(id) => console.log(`Add to cart: ${id}`)}
            onToggleFavorite={(id) => console.log(`Toggle favorite: ${id}`)}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">熱銷商品</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <FeaturedItem
            id="hot-1"
            name="膠原蛋白飲"
            description="30包裝 • 日本進口"
            price={1680}
            image="/placeholder.svg?height=60&width=60"
            buttonText="立即購買"
            onButtonClick={(id) => console.log(`Buy now: ${id}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export const ecommerceModule: AppModule = {
  config: {
    id: "ecommerce",
    name: "電商購物",
    icon: ShoppingBag,
    color: "green",
    description: "購買各種商品",
  },
  component: {
    id: "ecommerce",
    render: () => <EcommerceContent />,
  },
};
