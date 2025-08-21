import { ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Category } from "@/store/apis/ecommApi";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export const CategoryItem = ({
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
