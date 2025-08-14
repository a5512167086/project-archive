import { Category } from "@/store/apis/ecommApi";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const flattenCategories = (
  categories: Category[],
  indentation: string = "",
  level: number = 0
) => {
  let flattened: { label: string; value: string }[] = [];

  categories.forEach((category) => {
    const prefix = level > 0 ? `${indentation.repeat(level)}` : "";
    flattened.push({
      label: `${prefix}${category.category_name}`,
      value: String(category.class_id),
    });

    if (category.children && category.children.length > 0) {
      flattened = flattened.concat(
        flattenCategories(category.children, indentation, level + 1)
      );
    }
  });

  return flattened;
};
