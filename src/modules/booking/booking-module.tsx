import { useState } from "react";
import { Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SearchInput } from "../../components/SearchInput";
import { FeaturedItem } from "../../components/FeaturedItem";
import { BookingDialog } from "../../components/BookingDialog";
import {
  useGetReservationItemsQuery,
  type ReservationItem,
} from "../../store/api/reservationApi";
import { useLiff } from "../../hooks/useLiff";
import type { AppModule } from "../../types/module";

function BookingContent() {
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

  const handleBookingClick = (itemId: string) => {
    const item = reservationItemsData?.find(
      (item) => item.reservation_item_id === itemId
    );
    if (item) {
      setSelectedItem(item);
      setIsDialogOpen(true);
    }
  };

  const handleConfirmBooking = () => {
    console.log("預約確認完成:", {
      item: selectedItem?.reservation_name,
    });
    // 預約成功後可以執行的操作，比如刷新數據等
    // Toast 通知已經在 BookingDialog 中處理
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <SearchInput placeholder="搜尋服務..." />
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-gray-500">載入中...</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <SearchInput placeholder="搜尋服務..." />
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-red-500">載入服務失敗</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const reservationItems = reservationItemsData || [];

  return (
    <div className="space-y-4">
      <SearchInput placeholder="搜尋服務..." />
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            可預約服務 ({reservationItems.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {reservationItems.length === 0 ? (
            <div className="text-center text-gray-500 py-4">暫無可預約服務</div>
          ) : (
            reservationItems.map((item) => {
              // 檢查是否有額外付費選項
              const hasPayableOptions = item.option_groups.some((group) =>
                group.options.some((opt) => opt.price > 0)
              );

              return (
                <FeaturedItem
                  key={item.reservation_item_id}
                  id={item.reservation_item_id}
                  name={item.reservation_name}
                  description={
                    item.reservation_description ||
                    `${item.duration_minutes}分鐘`
                  }
                  price={item.price}
                  priceLabel={hasPayableOptions ? "起" : undefined}
                  buttonText="預約"
                  onButtonClick={handleBookingClick}
                />
              );
            })
          )}
        </CardContent>
      </Card>

      {/* 預約對話框 */}
      {selectedItem && (
        <BookingDialog
          reservationItem={selectedItem}
          isOpen={isDialogOpen}
          onClose={() => {
            setIsDialogOpen(false);
            setSelectedItem(null);
          }}
          onConfirm={handleConfirmBooking}
        />
      )}
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
