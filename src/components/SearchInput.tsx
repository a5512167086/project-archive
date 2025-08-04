import { Search, ListFilter } from "lucide-react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";

interface SearchInputProps {
  placeholder: string;
  value?: string;
  onChange?: (value: string) => void;
  onFilterClick?: () => void;
}

export function SearchInput({
  placeholder,
  value,
  onChange,
  onFilterClick,
}: SearchInputProps) {
  return (
    <div className="relative flex items-center gap-2">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder={placeholder}
          className="pl-10"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
        />
      </div>
      {onFilterClick && (
        <Button variant="outline" size="icon" onClick={onFilterClick}>
          <ListFilter className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
