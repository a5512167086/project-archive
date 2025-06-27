import { Search } from "lucide-react";
import { Input } from "./ui/input";

interface SearchInputProps {
  placeholder: string;
  value?: string;
  onChange?: (value: string) => void;
}

export function SearchInput({
  placeholder,
  value,
  onChange,
}: SearchInputProps) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
      <Input
        placeholder={placeholder}
        className="pl-10"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
      />
    </div>
  );
}
