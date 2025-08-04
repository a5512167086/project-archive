import { useState } from "react";
import { ShoppingBag, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "../../components/SearchInput";
import { ProductCard } from "../../components/ProductCard";
import type { AppModule } from "../../types/module";
import {
  useGetProductsQuery,
  useGetCategoriesQuery,
  type Category,
} from "../../store/api/ecommApi";
import { useLiff } from "../../hooks/useLiff";
import placeholder from "@/assets/placeholder.svg";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { CategoryFilterDialog } from "@/components/CategoryFilterDialog";

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

  if (productsLoading || categoriesLoading) {
    return <div>Loading...</div>;
  }

  if (productsError || categoriesError) {
    return <div>Error loading data</div>;
  }

  const filteredProducts = selectedCategoryId
    ? products?.filter((p) => p.category_id === selectedCategoryId)
    : products;

  return (
    <div className="space-y-4">
      <SearchInput
        placeholder="搜尋商品..."
        onFilterClick={() => setIsFilterOpen(true)}
      />

      <div className="grid grid-cols-2 gap-4">
        {filteredProducts?.map((product) => (
          <ProductCard
            key={product.product_id}
            id={product.product_id}
            name={product.product_name}
            price={product.price}
            rating={5} // Assuming a default rating
            image={placeholder}
            onAddToCart={(id) => console.log(`Add to cart: ${id}`)}
            onToggleFavorite={(id) => console.log(`Toggle favorite: ${id}`)}
          />
        ))}
      </div>
      <CategoryFilterDialog
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        categories={categories || []}
        selectedCategoryId={selectedCategoryId}
        onSelectCategory={setSelectedCategoryId}
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
