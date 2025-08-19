import { useSearchParams, Link } from "react-router";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { useGetUserOrdersQuery } from "../store/apis/userApi";
import { useLiff } from "../hooks/useLiff";
import type { UserOrder } from "../store/apis/userApi";
import { PackageSearch, X } from "lucide-react";
import { useGetProductsQuery } from "../store/apis/ecommApi";
import type { ProductsResponse } from "../store/apis/ecommApi";

// 狀態映射和顏色定義
const statusMap = {
  pending: { label: "待處理", className: "bg-orange-100 text-orange-800" },
  processing: { label: "處理中", className: "bg-blue-100 text-blue-800" },
  shipped: { label: "已出貨", className: "bg-purple-100 text-purple-800" },
  completed: { label: "已完成", className: "bg-green-100 text-green-800" },
  cancelled: { label: "已取消", className: "bg-red-100 text-red-800" },
};

const paymentStatusMap = {
  paid: { label: "已付款", className: "bg-green-100 text-green-800" },
  unpaid: { label: "未付款", className: "bg-red-100 text-red-800" },
  pending: { label: "付款處理中", className: "bg-yellow-100 text-yellow-800" },
};

// 詳情彈窗組件
function OrderDetailModal({
  order,
  isOpen,
  onClose,
  products,
}: {
  order: UserOrder;
  isOpen: boolean;
  onClose: () => void;
  products: ProductsResponse;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">訂單詳情</h2>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">訂單狀態：</span>
              <Badge
                className={
                  statusMap[order.status as keyof typeof statusMap]?.className
                }
              >
                {statusMap[order.status as keyof typeof statusMap]?.label ||
                  order.status}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">付款狀態：</span>
              <Badge
                className={
                  paymentStatusMap[
                    order.payment_status as keyof typeof paymentStatusMap
                  ]?.className
                }
              >
                {paymentStatusMap[
                  order.payment_status as keyof typeof paymentStatusMap
                ]?.label || order.payment_status}
              </Badge>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium text-gray-700">商品列表：</h4>
              <div className="bg-gray-50 p-3 rounded-md space-y-2">
                {order.items.map((item) => {
                  const product = products.find(
                    (p) => p.product_id === item.product_id
                  );
                  const variant = product?.variants.find(
                    (v) => v.variant_id === item.variant_id
                  );
                  const productName = product?.product_name || "商品不存在";
                  const price = variant?.price || product?.price || 0;

                  return (
                    <div
                      key={`${item.product_id}-${item.variant_id}`}
                      className="flex justify-between items-center"
                    >
                      <span>
                        {productName} x {item.quantity}
                      </span>
                      <span>${price * item.quantity}</span>
                    </div>
                  );
                })}
                <div className="flex justify-between items-center font-semibold border-t pt-2">
                  <span>總計：</span>
                  <span>${order.total_amount}</span>
                </div>
              </div>
            </div>

            {order.shipping_method !== "store_pickup" && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700">配送資訊：</h4>
                <div className="bg-gray-50 p-3 rounded-md space-y-1 text-sm">
                  <p>收件人: {order.recipient_name}</p>
                  <p>電話: {order.recipient_phone}</p>
                  <p>地址: {order.shipping_address}</p>
                  <p>配送方式: {order.shipping_method}</p>
                  {order.tracking_number && (
                    <p>追蹤編號: {order.tracking_number}</p>
                  )}
                </div>
              </div>
            )}

            <div className="text-xs text-gray-500 pt-2 border-t">
              訂單建立時間：
              {new Date(order.created_at).toLocaleString("zh-TW")}
            </div>
          </div>

          <div className="pt-4">
            <Button onClick={onClose} className="w-full">
              關閉
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

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
            <div className="text-center py-12 text-gray-500">
              <PackageSearch className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                沒有訂單
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                看來您還沒有下過任何訂單
              </p>
              <div className="mt-6">
                <Link to="/">
                  <Button>前往首頁</Button>
                </Link>
              </div>
            </div>
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
