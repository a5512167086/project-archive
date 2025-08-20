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
  disabled?: boolean; // 新增禁用狀態
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
  disabled = false,
  onButtonClick,
}: FeaturedItemProps) {
  return (
    <div
      className={`flex items-center border hover:shadow-md transition-shadow space-x-3 p-3 mx-2 rounded ${
        disabled ? "opacity-60" : ""
      }`}
    >
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
        {disabled && <p className="text-xs text-red-500 mt-1">暫停服務</p>}
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
        <Button
          size="sm"
          disabled={disabled}
          onClick={() => onButtonClick?.(id)}
        >
          {disabled ? "暫停服務" : buttonText}
        </Button>
      </div>
    </div>
  );
}
