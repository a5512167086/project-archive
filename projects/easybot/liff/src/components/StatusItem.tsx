import { Badge } from "@/components/ui/badge";

interface StatusItemProps {
  id: string;
  title: string;
  date: string;
  description: string;
  status: string;
  price: number;
  statusColor: "green" | "blue" | "orange" | "red";
}

const statusColorClasses = {
  green: "bg-green-100 text-green-800 border-green-500",
  blue: "bg-blue-100 text-blue-800 border-blue-500",
  orange: "bg-orange-100 text-orange-800 border-orange-500",
  red: "bg-red-100 text-red-800 border-red-500",
};

export function StatusItem({
  title,
  date,
  description,
  status,
  price,
  statusColor,
}: Omit<StatusItemProps, "id">) {
  return (
    <div className={`border-l-4 border-${statusColor}-500 pl-4`}>
      <div className="flex justify-between items-start">
        <div>
          <h4 className="font-medium">{title}</h4>
          <p className="text-sm text-muted-foreground">{date}</p>
          <p className="text-sm">{description}</p>
        </div>
        <div className="text-right">
          <Badge
            variant="secondary"
            className={statusColorClasses[statusColor]}
          >
            {status}
          </Badge>
          <p className="text-sm font-medium mt-1">${price}</p>
        </div>
      </div>
    </div>
  );
}
