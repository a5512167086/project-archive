import { useSearchParams, Link } from "react-router";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { StatusItem } from "../components/StatusItem";
import { useGetReservationsQuery } from "../store/api/reservationApi";

export default function AppointmentsPage() {
  const [searchParams] = useSearchParams();
  const filter = searchParams.get("status") || "all";

  // 使用 Redux Query 取得預約資料
  const {
    data: reservationsData,
    error,
    isLoading,
  } = useGetReservationsQuery({
    status: filter,
  });

  const appointments = reservationsData?.reservations || [];

  const statusFilters = [
    { key: "all", label: "全部", count: appointments.length },
    {
      key: "待確認",
      label: "待確認",
      count: appointments.filter((a) => a.status === "待確認").length,
    },
    {
      key: "已確認",
      label: "已確認",
      count: appointments.filter((a) => a.status === "已確認").length,
    },
    {
      key: "已完成",
      label: "已完成",
      count: appointments.filter((a) => a.status === "已完成").length,
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
    <div className="space-y-4">
      {/* 快速操作 */}
      <div className="flex space-x-2">
        <Button
          size="sm"
          onClick={() => (window.location.href = "/home?module=booking")}
          className="flex-1"
        >
          新增預約
        </Button>
        <Button size="sm" variant="outline" className="flex-1 bg-transparent">
          查看日曆
        </Button>
      </div>

      {/* 狀態篩選 */}
      <div className="flex space-x-2 overflow-x-auto pb-2">
        {statusFilters.map((statusFilter) => (
          <Link
            key={statusFilter.key}
            to={`/appointments${
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
            {filter === "all" ? "所有預約" : `${filter}預約`}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {appointments.length > 0 ? (
            appointments.map((appointment) => (
              <StatusItem
                key={appointment.id}
                title={appointment.title}
                date={appointment.date}
                description={appointment.description}
                status={appointment.status}
                price={appointment.price}
                statusColor={appointment.statusColor}
              />
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>沒有找到相關預約</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
