import { useState } from "react";
import { ShoppingBag, ShoppingCart } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "@/components/SearchInput";
import { ProductCard } from "@/components/features/ecommerce/components/ProductCard";
import type { AppModule } from "@/types/module";
import { ProductDialog } from "@/components/features/ecommerce/components/ProductDialog";
import {
  useGetProductsQuery,
  useGetCategoriesQuery,
  useGetBrandsQuery,
} from "@/store/apis/ecommApi";
import { useLiff } from "@/hooks/useLiff";
import placeholder from "@/assets/placeholder.svg";
import { FilterDialog } from "@/components/features/ecommerce/components/FilterDialog";
import { Link } from "react-router";
import { useAppSelector } from "@/store";
import { Button } from "@/components/ui/button";

function EcommerceContent() {
  const { botUUID } = useLiff();
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(
    null
  );
  const [selectedBrandId, setSelectedBrandId] = useState<number | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(
    null
  );
  const { items } = useAppSelector((state) => state.cart);

  const {
    data: products,
    isLoading: productsLoading,
    error: productsError,
  } = useGetProductsQuery(botUUID || "", { skip: !botUUID });
  const {
    data: categories,
    isLoading: categoriesLoading,
    error: categoriesError,
  } = useGetCategoriesQuery(botUUID || "", { skip: !botUUID });
  const {
    data: brands,
    isLoading: brandsLoading,
    error: brandsError,
  } = useGetBrandsQuery(botUUID || "", { skip: !botUUID });

  if (productsLoading || categoriesLoading || brandsLoading) {
    return <div>Loading...</div>;
  }

  if (productsError || categoriesError || brandsError) {
    return <div>Error loading data</div>;
  }

  const filteredProducts = products?.filter((p) => {
    const categoryMatch = selectedCategoryId
      ? p.category_id === selectedCategoryId
      : true;
    const brandMatch = selectedBrandId ? p.brand_id === selectedBrandId : true;
    return categoryMatch && brandMatch;
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center w-full space-x-2">
        <div className="flex-1">
          <SearchInput
            placeholder="搜尋商品..."
            onFilterClick={() => setIsFilterOpen(true)}
          />
        </div>

        <Link to="/cart">
          <Button variant="outline" size="icon" className="relative">
            <ShoppingCart className="h-5 w-5" />
            {items.length > 0 && (
              <Badge
                variant="destructive"
                className="absolute -top-2 -right-2 px-2 py-0.5 text-xs rounded-full"
              >
                {items.length}
              </Badge>
            )}
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {filteredProducts?.map((product) => {
          const images = product.images as
            | { image_url: string; is_primary?: boolean }[]
            | undefined;
          const primaryImage = images?.find((img) => img.is_primary);
          const imageUrl =
            primaryImage?.image_url || images?.[0]?.image_url || placeholder;
          return (
            <ProductCard
              key={product.product_id}
              id={product.product_id}
              name={product.product_name}
              price={product.price}
              image={imageUrl}
              onClick={() => setSelectedProductId(product.product_id)}
            />
          );
        })}
      </div>
      <FilterDialog
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        categories={categories || []}
        selectedCategoryId={selectedCategoryId}
        onSelectCategory={setSelectedCategoryId}
        brands={brands || []}
        selectedBrandId={selectedBrandId}
        onSelectBrand={setSelectedBrandId}
      />
      {selectedProductId && products && (
        <ProductDialog
          isOpen={!!selectedProductId}
          onClose={() => setSelectedProductId(null)}
          product={
            products.find((p) => p.product_id === selectedProductId) || null
          }
        />
      )}
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
