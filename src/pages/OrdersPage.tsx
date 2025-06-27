import { useSearchParams, Link } from "react-router";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { StatusItem } from "../components/StatusItem";

export default function OrdersPage() {
  const [searchParams] = useSearchParams();
  const filter = searchParams.get("status") || "all";

  // Mock data
  const orders = [
    {
      id: "12345",
      title: "訂單 #12345",
      date: "2024-01-15",
      description: "精華液套組 x1",
      status: "已完成",
      price: 899,
      statusColor: "green" as const,
    },
    {
      id: "12344",
      title: "訂單 #12344",
      date: "2024-01-12",
      description: "維他命C錠 x2",
      status: "配送中",
      price: 900,
      statusColor: "blue" as const,
    },
    {
      id: "12343",
      title: "訂單 #12343",
      date: "2024-01-10",
      description: "膠原蛋白飲 x1",
      status: "處理中",
      price: 1680,
      statusColor: "orange" as const,
    },
  ];

  const filteredOrders =
    filter === "all"
      ? orders
      : orders.filter((order) => order.status === filter);

  const statusFilters = [
    { key: "all", label: "全部", count: orders.length },
    {
      key: "處理中",
      label: "處理中",
      count: orders.filter((o) => o.status === "處理中").length,
    },
    {
      key: "配送中",
      label: "配送中",
      count: orders.filter((o) => o.status === "配送中").length,
    },
    {
      key: "已完成",
      label: "已完成",
      count: orders.filter((o) => o.status === "已完成").length,
    },
  ];

  return (
    <div className="space-y-4">
      {/* 狀態篩選 */}
      <div className="flex space-x-2 overflow-x-auto pb-2">
        {statusFilters.map((statusFilter) => (
          <Link
            key={statusFilter.key}
            to={`/orders${
              statusFilter.key !== "all" ? `?status=${statusFilter.key}` : ""
            }`}
            className="whitespace-nowrap"
          >
            <Badge
              variant={filter === statusFilter.key ? "default" : "outline"}
              className="cursor-pointer"
            >
              {statusFilter.label} ({statusFilter.count})
            </Badge>
          </Link>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {filter === "all" ? "所有訂單" : `${filter}訂單`}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {filteredOrders.length > 0 ? (
            filteredOrders.map((order) => (
              <StatusItem
                key={order.id}
                title={order.title}
                date={order.date}
                description={order.description}
                status={order.status}
                price={order.price}
                statusColor={order.statusColor}
              />
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>沒有找到相關訂單</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
