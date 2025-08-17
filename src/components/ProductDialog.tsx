import { useState, useEffect } from "react";
import { Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ImageCarousel } from "./ImageCarousel";
import { useAppDispatch, useAppSelector } from "@/store";
import { addToCart } from "@/store/modules/cartSlice";
import type { Product } from "@/store/apis/ecommApi";
import { DialogDescription } from "@radix-ui/react-dialog";
import { flattenCategories } from "@/lib/utils";

interface ProductDialogProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
}

export function ProductDialog({
  product,
  isOpen,
  onClose,
}: ProductDialogProps) {
  const [quantity, setQuantity] = useState(1);
  const { brands, categories } = useAppSelector((state) => state.ecomm);
  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(
    null
  );

  useEffect(() => {
    if (isOpen) {
      setQuantity(1);
      setSelectedVariantId(null);
    }
  }, [isOpen, product]);

  const dispatch = useAppDispatch();

  const handleAddToCart = () => {
    if (!product) return;
    dispatch(
      addToCart({
        productId: product.product_id,
        quantity,
        variantId: selectedVariantId,
      })
    );
    onClose();
  };

  const selectedVariant = product?.variants.find(
    (v) => v.variant_id === selectedVariantId
  );
  const price = selectedVariant?.price ?? product?.price;

  if (!isOpen || !product) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="h-full w-full max-w-none flex flex-col p-0 sm:max-w-none">
        <>
          <DialogDescription className="sr-only">
            {product.product_description || `${product.product_name} 詳細資訊`}
          </DialogDescription>
          <DialogHeader className="p-4 border-b">
            <DialogTitle>{product.product_name}</DialogTitle>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span>
                {
                  brands.find((brand) => brand.object_id == product.brand_id)
                    ?.brand_name
                }
              </span>
              <span>&bull;</span>
              <span>
                {
                  flattenCategories(categories).find(
                    (category) => category.value == String(product.category_id)
                  )?.label
                }
              </span>
            </div>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto">
            <ImageCarousel images={product.images} />
            <div className="space-y-4 p-4">
              <p className="text-sm text-muted-foreground">
                {product.product_description}
              </p>
              <div className="text-2xl font-bold">${price}</div>
              {product.variants && product.variants.length > 0 && (
                <Select
                  onValueChange={(value) =>
                    setSelectedVariantId(value === "null" ? null : value)
                  }
                  value={selectedVariantId || "null"}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="選擇規格" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="null">預設</SelectItem>
                    {product.variants.map((variant) => (
                      <SelectItem
                        key={variant.variant_id}
                        value={variant.variant_id}
                      >
                        {variant.variant_name}
                        {variant.price != null && ` (${variant.price})`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <div className="flex items-center justify-between">
                <p>數量</p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <span>{quantity}</span>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setQuantity(quantity + 1)}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter className="p-4 border-t">
            <Button onClick={handleAddToCart} className="w-full">
              加入購物車
            </Button>
          </DialogFooter>
        </>
      </DialogContent>
    </Dialog>
  );
}
