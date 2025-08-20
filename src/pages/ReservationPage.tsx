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
import { useGetUserReservationsQuery } from "../store/apis/userApi";
import { useLiff } from "../hooks/useLiff";
import type { UserReservation } from "../store/apis/userApi";

// 狀態映射和顏色定義
const statusMap = {
  pending: { label: "待確認", color: "orange" as const },
  confirmed: { label: "已確認", color: "blue" as const },
  cancelled: { label: "已取消", color: "red" as const },
  completed: { label: "已完成", color: "green" as const },
};

import { ReservationDetailModal } from "@/components/features/reservations/components/ReservationDetailModal";
import { EmptyState } from "@/components/common/EmptyState";
import { PackageSearch } from "lucide-react";

export default function ReservationPage() {
  const [searchParams] = useSearchParams();
  const [selectedReservation, setSelectedReservation] =
    useState<UserReservation | null>(null);
  const filter = searchParams.get("status") || "all";
  const { botUUID } = useLiff();

  // 使用新的用戶預約API
  const {
    data: userReservations,
    error,
    isLoading,
  } = useGetUserReservationsQuery(botUUID || "", { skip: !botUUID });

  const reservations = userReservations || [];

  // 按時間排序（最近的在前）
  const sortedReservations = [...reservations].sort((a, b) => {
    const dateTimeA = new Date(
      `${a.reservation_date}T${a.start_time}`
    ).getTime();
    const dateTimeB = new Date(
      `${b.reservation_date}T${b.start_time}`
    ).getTime();
    return dateTimeB - dateTimeA; // 降序排列，最近的在前
  });

  // 根據篩選條件過濾預約
  const filteredReservations =
    filter === "all"
      ? sortedReservations
      : sortedReservations.filter(
          (reservation) => reservation.status === filter
        );

  const statusFilters = [
    { key: "all", label: "全部", count: sortedReservations.length },
    {
      key: "pending",
      label: "待確認",
      count: sortedReservations.filter((r) => r.status === "pending").length,
    },
    {
      key: "confirmed",
      label: "已確認",
      count: sortedReservations.filter((r) => r.status === "confirmed").length,
    },
    {
      key: "completed",
      label: "已完成",
      count: sortedReservations.filter((r) => r.status === "completed").length,
    },
    {
      key: "cancelled",
      label: "已取消",
      count: sortedReservations.filter((r) => r.status === "cancelled").length,
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8">
          <p>載入中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8 text-red-500">
          <p>載入預約時發生錯誤</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      {/* 狀態篩選 */}
      <div className="flex space-x-2 overflow-x-auto pb-2">
        {statusFilters.map((statusFilter) => (
          <Link
            key={statusFilter.key}
            to={`/reservation${
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
              ? "所有預約"
              : `${
                  statusMap[filter as keyof typeof statusMap]?.label || filter
                }預約`}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {filteredReservations.length > 0 ? (
            filteredReservations.map((reservation) => {
              const formatDate = (date: string) => {
                return new Date(date).toLocaleDateString("zh-TW", {
                  year: "numeric",
                  month: "numeric",
                  day: "numeric",
                  weekday: "short",
                });
              };

              const formatTime = (startTime: string, endTime: string) => {
                const formattedStartTime = startTime.slice(0, 5);
                const formattedEndTime = endTime.slice(0, 5);
                return `${formattedStartTime} - ${formattedEndTime}`;
              };

              return (
                <div
                  key={reservation.reservation_id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow mx-2"
                >
                  <div className="flex items-center justify-between">
                    {/* 左側：預約資訊 */}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-lg text-gray-900">
                          {reservation.service_name}
                        </h3>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-gray-600 font-medium">
                          📅 {formatDate(reservation.reservation_date)}
                        </p>
                        <p className="text-sm text-gray-600">
                          🕒{" "}
                          {formatTime(
                            reservation.start_time,
                            reservation.end_time
                          )}
                        </p>
                      </div>
                    </div>

                    {/* 右側：狀態和按鈕 */}
                    <div className="flex flex-col items-end space-y-3 ml-6">
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
                          text-xs px-3 py-1
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

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedReservation(reservation)}
                        className="text-xs px-3 py-1 h-8"
                      >
                        查看詳情
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <EmptyState
              icon={
                <PackageSearch className="mx-auto h-12 w-12 text-gray-400" />
              }
              title="沒有找到相關預約"
              description="您似乎還沒有任何預約紀錄"
              actionText="前往預約"
              actionTo="/home?module=reservation"
            />
          )}
        </CardContent>
      </Card>

      {/* 詳情彈窗 */}
      {selectedReservation && (
        <ReservationDetailModal
          reservation={selectedReservation}
          isOpen={true}
          onClose={() => setSelectedReservation(null)}
        />
      )}
    </div>
  );
}
