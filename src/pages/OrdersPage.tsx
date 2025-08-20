import { useSearchParams, Link } from "react-router";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useGetUserOrdersQuery } from "@/store/apis/userApi";
import { useLiff } from "@/hooks/useLiff";
import type { UserOrder } from "@/store/apis/userApi";
import { PackageSearch } from "lucide-react";
import { useGetProductsQuery } from "@/store/apis/ecommApi";
import { OrderDetailModal } from "@/components/features/orders/components/OrderDetailModal";
import { EmptyState } from "@/components/common/EmptyState";

// 狀態映射和顏色定義
const statusMap = {
  pending: { label: "待處理", className: "bg-orange-100 text-orange-800" },
  processing: { label: "處理中", className: "bg-blue-100 text-blue-800" },
  shipped: { label: "已出貨", className: "bg-purple-100 text-purple-800" },
  completed: { label: "已完成", className: "bg-green-100 text-green-800" },
  cancelled: { label: "已取消", className: "bg-red-100 text-red-800" },
};

export default function OrdersPage() {
  const [searchParams] = useSearchParams();
  const [selectedOrder, setSelectedOrder] = useState<UserOrder | null>(null);
  const filter = searchParams.get("status") || "all";
  const { botUUID } = useLiff();
  const { data: products } = useGetProductsQuery(botUUID || "", {
    skip: !botUUID,
  });

  const {
    data: userOrders,
    error,
    isLoading,
  } = useGetUserOrdersQuery(botUUID || "", { skip: !botUUID });

  const orders = userOrders || [];

  const sortedOrders = [...orders].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const filteredOrders =
    filter === "all"
      ? sortedOrders
      : sortedOrders.filter((order) => order.status === filter);

  const statusFilters = [
    { key: "all", label: "全部", count: sortedOrders.length },
    ...Object.entries(statusMap).map(([key, { label }]) => ({
      key,
      label,
      count: sortedOrders.filter((o) => o.status === key).length,
    })),
  ];

  if (isLoading) {
    return <div className="text-center py-8">載入中...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">載入訂單時發生錯誤</div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
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

      <Card className="flex flex-col flex-1">
        <CardHeader>
          <CardTitle className="text-lg">
            {filter === "all"
              ? "所有訂單"
              : `${statusMap[filter as keyof typeof statusMap]?.label}訂單`}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 mx-2">
          {filteredOrders.length > 0 ? (
            filteredOrders.map((order) => (
              <div
                key={order.order_id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 space-y-2">
                    <h3 className="font-semibold text-lg text-gray-900">
                      訂單 #{order.order_id.slice(-6)}
                    </h3>
                    <p className="text-sm text-gray-600 font-medium">
                      📅 {new Date(order.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex flex-col items-end space-y-3 ml-6">
                    <Badge
                      className={`text-xs px-3 py-1 ${
                        statusMap[order.status as keyof typeof statusMap]
                          ?.className
                      }`}
                    >
                      {statusMap[order.status as keyof typeof statusMap]
                        ?.label || order.status}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedOrder(order)}
                      className="text-xs px-3 py-1 h-8"
                    >
                      查看詳情
                    </Button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <EmptyState
              icon={
                <PackageSearch className="mx-auto h-12 w-12 text-gray-400" />
              }
              title="沒有訂單"
              description="看來您還沒有下過任何訂單"
              actionText="前往首頁"
              actionTo="/"
            />
          )}
        </CardContent>
      </Card>

      {selectedOrder && products && (
        <OrderDetailModal
          order={selectedOrder}
          isOpen={true}
          onClose={() => setSelectedOrder(null)}
          products={products}
        />
      )}
    </div>
  );
}
