import { Button } from "@/components/ui/button";
import placeholder from "@/assets/placeholder.svg";

interface FeaturedItemProps {
  id: string;
  name: string;
  description: string;
  price: number;
  priceLabel?: string; // 例如 "起" 表示有額外選項
  image?: string;
  buttonText: string;
  onButtonClick?: (id: string) => void;
}

export function FeaturedItem({
  id,
  name,
  description,
  price,
  priceLabel,
  image,
  buttonText,
  onButtonClick,
}: FeaturedItemProps) {
  return (
    <div className="flex items-center space-x-3">
      <img
        src={image || placeholder}
        alt={name}
        width={60}
        height={60}
        className="rounded-lg object-cover"
      />
      <div className="flex-1">
        <h4 className="font-medium">{name}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="text-right">
        <p className="font-medium">
          ${price}
          {priceLabel && (
            <span className="text-sm text-muted-foreground ml-1">
              {priceLabel}
            </span>
          )}
        </p>
        <Button size="sm" onClick={() => onButtonClick?.(id)}>
          {buttonText}
        </Button>
      </div>
    </div>
  );
}
