import { X, Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Category } from "../store/api/ecommApi";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface CategoryFilterDialogProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  selectedCategoryId: number | null;
  onSelectCategory: (id: number | null) => void;
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

export function CategoryFilterDialog({
  isOpen,
  onClose,
  categories,
  selectedCategoryId,
  onSelectCategory,
}: CategoryFilterDialogProps) {
  if (!isOpen) return null;

  const handleSelectAndClose = (id: number | null) => {
    onSelectCategory(id);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col h-screen">
      {/* Header */}
      <div className="border-b bg-white p-4 flex-shrink-0 flex items-center justify-between">
        <h2 className="text-lg font-semibold">選擇分類</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-5 w-5" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <div
          className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-100 cursor-pointer"
          onClick={() => handleSelectAndClose(null)}
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
            onSelectCategory={handleSelectAndClose}
          />
        ))}
      </div>
    </div>
  );
}