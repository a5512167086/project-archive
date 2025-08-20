import { X, Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Category, Brand } from "@/store/apis/ecommApi";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface FilterDialogProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  selectedCategoryId: number | null;
  onSelectCategory: (id: number | null) => void;
  brands: Brand[];
  selectedBrandId: number | null;
  onSelectBrand: (id: number | null) => void;
}

const CategoryRecursive = ({
  category,
  selectedCategoryId,
  onSelectCategory,
}: {
  category: Category;
  selectedCategoryId: number | null;
  onSelectCategory: (id: number | null) => void;
}) => {
  const isSelected = category.class_id === selectedCategoryId;

  const handleSelect = () => {
    onSelectCategory(category.class_id);
  };

  return (
    <Collapsible>
      <div className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-100">
        <div
          className="flex-1 flex items-center justify-between cursor-pointer"
          onClick={handleSelect}
        >
          <span>{category.category_name}</span>
          {isSelected && <Check className="h-4 w-4 text-blue-600" />}
        </div>
        {category.children && category.children.length > 0 && (
          <CollapsibleTrigger className="ml-2 p-1">
            <ChevronDown className="h-4 w-4" />
          </CollapsibleTrigger>
        )}
      </div>
      {category.children && category.children.length > 0 && (
        <CollapsibleContent className="ml-6 mt-1 space-y-1 border-l pl-4">
          {category.children.map((child) => (
            <CategoryRecursive
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

const BrandList = ({
  brands,
  selectedBrandId,
  onSelectBrand,
}: {
  brands: Brand[];
  selectedBrandId: number | null;
  onSelectBrand: (id: number | null) => void;
}) => (
  <div>
    <h3 className="text-md font-semibold mb-2">品牌</h3>
    <div
      className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-100 cursor-pointer"
      onClick={() => onSelectBrand(null)}
    >
      <span>全部品牌</span>
      {selectedBrandId === null && <Check className="h-4 w-4 text-blue-600" />}
    </div>
    {brands.map((brand) => {
      const isSelected = brand.object_id === selectedBrandId;
      return (
        <div
          key={brand.object_id}
          className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-100 cursor-pointer"
          onClick={() => onSelectBrand(brand.object_id)}
        >
          <span>{brand.brand_name}</span>
          {isSelected && <Check className="h-4 w-4 text-blue-600" />}
        </div>
      );
    })}
  </div>
);

export function FilterDialog({
  isOpen,
  onClose,
  categories,
  selectedCategoryId,
  onSelectCategory,
  brands,
  selectedBrandId,
  onSelectBrand,
}: FilterDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col h-screen">
      <div className="border-b bg-white p-4 flex-shrink-0 flex items-center justify-between">
        <h2 className="text-lg font-semibold">篩選</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <BrandList
          brands={brands}
          selectedBrandId={selectedBrandId}
          onSelectBrand={onSelectBrand}
        />
        <div>
          <h3 className="text-md font-semibold mb-2">分類</h3>
          <div
            className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-100 cursor-pointer"
            onClick={() => onSelectCategory(null)}
          >
            <span>全部商品</span>
            {selectedCategoryId === null && (
              <Check className="h-4 w-4 text-blue-600" />
            )}
          </div>
          {categories.map((category) => (
            <CategoryRecursive
              key={category.class_id}
              category={category}
              selectedCategoryId={selectedCategoryId}
              onSelectCategory={onSelectCategory}
            />
          ))}
        </div>
      </div>

      <div className="border-t p-4">
        <Button className="w-full mb-2" onClick={onClose}>
          套用
        </Button>
      </div>
    </div>
  );
}
