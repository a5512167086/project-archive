import { Button } from "@/components/ui/button";
import { Link } from "react-router";

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionText: string;
  actionTo: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionText,
  actionTo,
}: EmptyStateProps) {
  return (
    <div className="text-center py-12 text-gray-500">
      <div className="mx-auto h-12 w-12 text-gray-400">{icon}</div>
      <h3 className="mt-2 text-sm font-medium text-gray-900">{title}</h3>
      <p className="mt-1 text-sm text-gray-500">{description}</p>
      <div className="mt-6">
        <Link to={actionTo}>
          <Button>{actionText}</Button>
        </Link>
      </div>
    </div>
  );
}
