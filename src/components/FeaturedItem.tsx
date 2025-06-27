import { Star } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FeaturedItemProps {
  id: string;
  name: string;
  description: string;
  price: number;
  rating: number;
  reviewCount: number;
  image: string;
  buttonText: string;
  onButtonClick?: (id: string) => void;
}

export function FeaturedItem({
  id,
  name,
  description,
  price,
  rating,
  reviewCount,
  image,
  buttonText,
  onButtonClick,
}: FeaturedItemProps) {
  return (
    <div className="flex items-center space-x-3">
      <img
        src={image || "/placeholder.svg"}
        alt={name}
        width={60}
        height={60}
        className="rounded-lg object-cover"
      />
      <div className="flex-1">
        <h4 className="font-medium">{name}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="flex items-center space-x-1">
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
          <span className="text-sm">{rating}</span>
          <span className="text-sm text-muted-foreground">({reviewCount})</span>
        </div>
      </div>
      <div className="text-right">
        <p className="font-medium">${price}</p>
        <Button size="sm" onClick={() => onButtonClick?.(id)}>
          {buttonText}
        </Button>
      </div>
    </div>
  );
}
