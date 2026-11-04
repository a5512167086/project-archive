import { Card, CardContent } from "./ui/card";

interface ProductCardProps {
  id: string;
  name: string;
  price: number;
  image: string;
  onClick: () => void;
}

export function ProductCard({ name, price, image, onClick }: ProductCardProps) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardContent className="p-3">
        <div className="relative">
          <img
            src={image || "https://via.placeholder.com/120"}
            alt={name}
            className="w-full h-32 object-cover rounded-lg mb-2"
          />
        </div>
        <h3 className="font-medium text-sm mb-1">{name}</h3>
        <div className="flex items-center justify-between">
          <span className="font-medium text-red-600">${price}</span>
        </div>
      </CardContent>
    </Card>
  );
}
