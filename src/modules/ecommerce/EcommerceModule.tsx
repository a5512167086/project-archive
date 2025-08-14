import { useState } from "react";
import { ShoppingBag, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "../../components/SearchInput";
import { ProductCard } from "../../components/ProductCard";
import type { AppModule } from "../../types/module";
import {
  useGetProductsQuery,
  useGetCategoriesQuery,
  useGetBrandsQuery,
  type Category,
} from "../../store/apis/ecommApi";
import { useLiff } from "../../hooks/useLiff";
import placeholder from "@/assets/placeholder.svg";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { FilterDialog } from "@/components/FilterDialog";

const CategoryItem = ({
  category,
  selectedCategoryId,
  onSelectCategory,
}: {
  category: Category;
  selectedCategoryId: number | null;
  onSelectCategory: (id: number | null) => void;
}) => {
  const isSelected = category.class_id === selectedCategoryId;

  return (
    <Collapsible>
      <div className="flex items-center justify-between">
        <Badge
          variant={isSelected ? "secondary" : "outline"}
          className="whitespace-nowrap cursor-pointer"
          onClick={() => onSelectCategory(category.class_id)}
        >
          {category.category_name}
        </Badge>
        {category.children && category.children.length > 0 && (
          <CollapsibleTrigger>
            <ChevronDown className="h-4 w-4" />
          </CollapsibleTrigger>
        )}
      </div>
      {category.children && category.children.length > 0 && (
        <CollapsibleContent className="ml-4 mt-2 space-y-2">
          {category.children.map((child) => (
            <CategoryItem
              key={child.class_id}
              category={child}
              selectedCategoryId={selectedCategoryId}
              onSelectCategory={onSelectCategory}
            />
          ))}
        </CollapsibleContent>
      )}
    </Collapsible>
  );
};

function EcommerceContent() {
  const { botUUID } = useLiff();
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(
    null
  );
  const [selectedBrandId, setSelectedBrandId] = useState<number | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

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
      <SearchInput
        placeholder="搜尋商品..."
        onFilterClick={() => setIsFilterOpen(true)}
      />

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
