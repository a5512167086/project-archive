import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { UserReservation } from "@/store/apis/userApi";

// 狀態映射和顏色定義
const statusMap = {
  pending: { label: "待確認", color: "orange" as const },
  confirmed: { label: "已確認", color: "blue" as const },
  cancelled: { label: "已取消", color: "red" as const },
  completed: { label: "已完成", color: "green" as const },
};

// 付款狀態映射
const paymentStatusMap = {
  paid: "已付款",
  unpaid: "未付款",
  pending: "付款中",
};

// 詳情彈窗組件
export function ReservationDetailModal({
  reservation,
  isOpen,
  onClose,
}: {
  reservation: UserReservation;
  isOpen: boolean;
  onClose: () => void;
}) {
  if (!isOpen) return null;

  const formatDateTime = (date: string, startTime: string, endTime: string) => {
    const formattedDate = new Date(date).toLocaleDateString("zh-TW", {
      year: "numeric",
      month: "numeric",
      day: "numeric",
      weekday: "short",
    });
    const formattedStartTime = startTime.slice(0, 5);
    const formattedEndTime = endTime.slice(0, 5);
    return `${formattedDate} ${formattedStartTime}-${formattedEndTime}`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 space-y-4">
          {/* 標題 */}
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">預約詳情</h2>
            <Button variant="ghost" size="sm" onClick={onClose}>
              ✕
            </Button>
          </div>

          {/* 服務資訊 */}
          <div className="space-y-3">
            <div>
              <h3 className="font-medium text-lg">
                {reservation.service_name}
              </h3>
              <p className="text-gray-600">
                {formatDateTime(
                  reservation.reservation_date,
                  reservation.start_time,
                  reservation.end_time
                )}
              </p>
            </div>

            {/* 狀態 */}
            <div className="flex items-center justify-between">
              <span className="text-gray-700">預約狀態：</span>
              <Badge
                variant={
                  reservation.status === "confirmed"
                    ? "default"
                    : reservation.status === "completed"
                    ? "secondary"
                    : reservation.status === "cancelled"
                    ? "destructive"
                    : "outline"
                }
                className={`
                  ${
                    reservation.status === "pending"
                      ? "bg-orange-50 text-orange-700 border-orange-200"
                      : ""
                  }
                  ${
                    reservation.status === "confirmed"
                      ? "bg-blue-50 text-blue-700 border-blue-200"
                      : ""
                  }
                  ${
                    reservation.status === "completed"
                      ? "bg-green-50 text-green-700 border-green-200"
                      : ""
                  }
                `}
              >
                {statusMap[reservation.status as keyof typeof statusMap]
                  ?.label || reservation.status}
              </Badge>
            </div>

            {/* 付款狀態 - 只有非現金付款才顯示 */}
            {reservation.payment_method !== "cash" && (
              <div className="flex items-center justify-between">
                <span className="text-gray-700">付款狀態：</span>
                <Badge
                  variant="outline"
                  className={`
                    ${
                      reservation.payment_status === "paid"
                        ? "bg-green-50 text-green-700 border-green-200"
                        : ""
                    }
                    ${
                      reservation.payment_status === "unpaid"
                        ? "bg-red-50 text-red-700 border-red-200"
                        : ""
                    }
                    ${
                      reservation.payment_status === "pending"
                        ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                        : ""
                    }
                  `}
                >
                  {
                    paymentStatusMap[
                      (reservation.payment_status ||
                        "unpaid") as keyof typeof paymentStatusMap
                    ]
                  }
                </Badge>
              </div>
            )}

            {/* 付款方式 */}
            <div className="flex items-center justify-between">
              <span className="text-gray-700">付款方式：</span>
              <span className="text-gray-900">
                {reservation.payment_method === "cash"
                  ? "現金"
                  : reservation.payment_method === "bank_transfer"
                  ? "銀行轉帳"
                  : reservation.payment_method}
              </span>
            </div>

            {/* 價格資訊 */}
            <div className="space-y-2">
              <h4 className="font-medium text-gray-700">價格資訊：</h4>
              <div className="bg-gray-50 p-3 rounded-md space-y-2">
                {/* 顯示有價格的選項 */}
                {reservation.selected_option_groups &&
                  reservation.selected_option_groups.some((group) =>
                    group.selected_options.some(
                      (option) => option.price && option.price > 0
                    )
                  ) && (
                    <div className="space-y-1">
                      <span className="text-gray-600 text-sm">附加選項：</span>
                      {reservation.selected_option_groups.map(
                        (group, groupIndex) =>
                          group.selected_options.map((option, optionIndex) =>
                            option.price && option.price > 0 ? (
                              <div
                                key={`${groupIndex}-${optionIndex}`}
                                className="flex items-center justify-between text-sm ml-2"
                              >
                                <span className="text-gray-600">
                                  • {option.option_name}：
                                </span>
                                <span className="font-medium">
                                  ${option.price}
                                </span>
                              </div>
                            ) : null
                          )
                      )}
                    </div>
                  )}

                {reservation.price && (
                  <div className="flex items-center justify-between text-base font-semibold border-t pt-2">
                    <span className="text-gray-800">總計：</span>
                    <span className="text-blue-600">${reservation.price}</span>
                  </div>
                )}
              </div>
            </div>

            {/* 選項詳情 */}
            {reservation.selected_option_groups &&
              reservation.selected_option_groups.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-700">選擇項目：</h4>
                  <div className="space-y-2">
                    {reservation.selected_option_groups.map((group, index) => (
                      <div key={index} className="bg-gray-50 p-3 rounded-md">
                        <h5 className="font-medium text-sm text-gray-800">
                          {group.group_name}
                        </h5>
                        <div className="mt-1 space-y-1">
                          {group.selected_options.map((option, optionIndex) => (
                            <div
                              key={optionIndex}
                              className="text-sm text-gray-600 flex items-center justify-between"
                            >
                              <span>• {option.option_name}</span>
                              {option.price && option.price > 0 && (
                                <span className="text-xs text-gray-500">
                                  +${option.price}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* 備註 */}
            {reservation.notes && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700">備註：</h4>
                <div className="bg-gray-50 p-3 rounded-md">
                  <p className="text-sm text-gray-700">{reservation.notes}</p>
                </div>
              </div>
            )}

            {/* 預約時間 */}
            <div className="text-xs text-gray-500 pt-2 border-t">
              預約建立時間：
              {new Date(reservation.created_at).toLocaleString("zh-TW")}
            </div>
          </div>

          {/* 關閉按鈕 */}
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
