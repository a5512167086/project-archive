import { useState } from "react";
import { Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SearchInput } from "../../components/SearchInput";
import { FeaturedItem } from "../../components/FeaturedItem";
import { ReservationDialog } from "../../components/ReservationDialog";
import {
  useGetReservationItemsQuery,
  type ReservationItem,
} from "../../store/api/reservationApi";
import { useLiff } from "../../hooks/useLiff";
import type { AppModule } from "../../types/module";

function ReservationContent() {
  const { botUUID } = useLiff();
  const [selectedItem, setSelectedItem] = useState<ReservationItem | null>(
    null
  );
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const {
    data: reservationItemsData,
    isLoading,
    error,
  } = useGetReservationItemsQuery(botUUID || "", { skip: !botUUID });

  const handleReservationClick = (itemId: string) => {
    const item = reservationItemsData?.find(
      (item) => item.service_id === itemId
    );
    if (item) {
      // 檢查項目的 is_active 狀態
      // 如果項目本身是 inactive，或者所有必需的選項組都是 inactive，則禁用項目
      const hasActiveRequiredOptionGroups = item.option_groups
        .filter((group) => group.is_required)
        .every(
          (group) =>
            group.is_active && group.options.some((opt) => opt.is_active)
        );

      const isItemDisabled =
        !item.is_active ||
        (item.option_groups.some((group) => group.is_required) &&
          !hasActiveRequiredOptionGroups);

      // 如果項目被禁用，則不執行任何操作
      if (isItemDisabled) {
        return;
      }

      setSelectedItem(item);
      setIsDialogOpen(true);
    }
  };

  const handleConfirmReservation = () => {
    console.log("預約確認完成:", {
      item: selectedItem?.service_name,
    });
    // 預約成功後可以執行的操作，比如刷新數據等
    // Toast 通知已經在 ReservationDialog 中處理
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full space-y-4">
        <SearchInput placeholder="搜尋服務..." />
        <Card className="flex-1 flex flex-col">
          <CardContent className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-500">載入中...</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full space-y-4">
        <SearchInput placeholder="搜尋服務..." />
        <Card className="flex-1 flex flex-col">
          <CardContent className="flex-1 flex items-center justify-center">
            <div className="text-center text-red-500">載入服務失敗</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const reservationItems = reservationItemsData || [];

  return (
    <div className="flex flex-col h-full space-y-4">
      <SearchInput placeholder="搜尋服務..." />
      <Card className="flex-1 flex flex-col">
        <CardHeader>
          <CardTitle className="text-lg">
            可預約服務 ({reservationItems.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col space-y-3">
          {reservationItems.length === 0 ? (
            <div className="text-center text-gray-500 py-4">暫無可預約服務</div>
          ) : (
            reservationItems.map((item) => {
              // 檢查是否有額外付費選項
              const hasPayableOptions = item.option_groups.some((group) =>
                group.options.some((opt) => opt.price > 0)
              );

              // 檢查項目的 is_active 狀態
              // 如果項目本身是 inactive，或者所有必需的選項組都是 inactive，則禁用項目
              const hasActiveRequiredOptionGroups = item.option_groups
                .filter((group) => group.is_required)
                .every(
                  (group) =>
                    group.is_active &&
                    group.options.some((opt) => opt.is_active)
                );

              const isItemDisabled =
                !item.is_active ||
                (item.option_groups.some((group) => group.is_required) &&
                  !hasActiveRequiredOptionGroups);

              return (
                <FeaturedItem
                  key={item.service_id}
                  id={item.service_id}
                  name={item.service_name}
                  description={
                    item.service_description || `${item.duration_minutes}分鐘`
                  }
                  price={item.price}
                  priceLabel={hasPayableOptions ? "起" : undefined}
                  buttonText="預約"
                  disabled={isItemDisabled}
                  onButtonClick={handleReservationClick}
                />
              );
            })
          )}
        </CardContent>
      </Card>

      {/* 預約對話框 */}
      {selectedItem && (
        <ReservationDialog
          reservationItem={selectedItem}
          isOpen={isDialogOpen}
          onClose={() => {
            setIsDialogOpen(false);
            setSelectedItem(null);
          }}
          onConfirm={handleConfirmReservation}
        />
      )}
    </div>
  );
}

export const reservationModule: AppModule = {
  config: {
    id: "reservation",
    name: "預約服務",
    icon: Calendar,
    color: "blue",
    description: "預約各種專業服務",
  },
  component: {
    id: "reservation",
    render: () => <ReservationContent />,
  },
};
