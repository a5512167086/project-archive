import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface QuickActionCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  color: "blue" | "green" | "red" | "purple";
  onClick?: () => void;
}

const colorClasses = {
  blue: "text-blue-600",
  green: "text-green-600",
  red: "text-red-600",
  purple: "text-purple-600",
};

export function QuickActionCard({
  icon: Icon,
  title,
  description,
  color,
  onClick,
}: QuickActionCardProps) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardContent className="p-4 text-center">
        <Icon className={`h-8 w-8 mx-auto mb-2 ${colorClasses[color]}`} />
        <h3 className="font-medium">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}
