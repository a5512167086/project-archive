import { Heart, Star, Plus } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";

interface ProductCardProps {
  id: string;
  name: string;
  price: number;
  rating: number;
  image: string;
  onAddToCart?: (id: string) => void;
  onToggleFavorite?: (id: string) => void;
  isFavorite?: boolean;
}

export function ProductCard({
  id,
  name,
  price,
  rating,
  image,
  onAddToCart,
  onToggleFavorite,
  isFavorite = false,
}: ProductCardProps) {
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow">
      <CardContent className="p-3">
        <div className="relative">
          <img
            src={image || "https://via.placeholder.com/120"}
            alt={name}
            className="w-full h-32 object-cover rounded-lg mb-2"
          />
          <Button
            size="icon"
            variant="ghost"
            className="absolute top-1 right-1 h-8 w-8"
            onClick={(e) => {
              e.stopPropagation();
              onToggleFavorite?.(id);
            }}
          >
            <Heart
              className={`h-4 w-4 ${
                isFavorite ? "fill-red-500 text-red-500" : ""
              }`}
            />
          </Button>
        </div>
        <h3 className="font-medium text-sm mb-1">{name}</h3>
        <div className="flex items-center space-x-1 mb-1">
          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
          <span className="text-xs">{rating}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-medium text-red-600">${price}</span>
          <Button
            size="sm"
            className="h-7 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onAddToCart?.(id);
            }}
          >
            <Plus className="h-3 w-3 mr-1" />
            加入購物車
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
