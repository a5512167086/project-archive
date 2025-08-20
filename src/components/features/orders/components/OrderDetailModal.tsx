import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { UserOrder } from "@/store/apis/userApi";
import type { ProductsResponse } from "@/store/apis/ecommApi";
import { X } from "lucide-react";

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
export function OrderDetailModal({
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
