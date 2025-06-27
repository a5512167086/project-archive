import { Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SearchInput } from "../../components/SearchInput";
import { ServiceCard } from "../../components/ServiceCard";
import { FeaturedItem } from "../../components/FeaturedItem";
import type { AppModule } from "../../types/module";

const services = [
  {
    id: "1",
    icon: Calendar,
    title: "美容護理",
    description: "專業美容服務",
    color: "blue" as const,
  },
  {
    id: "2",
    icon: Calendar,
    title: "按摩服務",
    description: "放鬆身心",
    color: "green" as const,
  },
  {
    id: "3",
    icon: Calendar,
    title: "健身教練",
    description: "一對一指導",
    color: "purple" as const,
  },
  {
    id: "4",
    icon: Calendar,
    title: "醫療諮詢",
    description: "專業醫師",
    color: "orange" as const,
  },
];

function BookingContent() {
  return (
    <div className="space-y-4">
      <SearchInput placeholder="搜尋服務..." />

      <div className="grid grid-cols-2 gap-4">
        {services.map((service) => (
          <ServiceCard
            key={service.id}
            icon={service.icon}
            title={service.title}
            description={service.description}
            color={service.color}
            onClick={() => console.log(`Selected service: ${service.title}`)}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">推薦服務</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <FeaturedItem
            id="featured-1"
            name="深層清潔護理"
            description="90分鐘 • 專業美容師"
            price={1200}
            rating={4.8}
            reviewCount={128}
            image="/placeholder.svg?height=60&width=60"
            buttonText="預約"
            onButtonClick={(id) => console.log(`Book service: ${id}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export const bookingModule: AppModule = {
  config: {
    id: "booking",
    name: "預約服務",
    icon: Calendar,
    color: "blue",
    description: "預約各種專業服務",
  },
  component: {
    id: "booking",
    render: () => <BookingContent />,
  },
};
