import { useState, useEffect } from "react";
import {
  Calendar,
  Clock,
  ChevronLeft,
  ChevronRight,
  Settings,
  MessageSquare,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useGetAvailableTimesQuery,
  useCreateNewReservationMutation,
  type ReservationItem,
  type CreateReservationOptionValue,
} from "../store/api/reservationApi";
import { useLiff } from "../hooks/useLiff";
import { useToast } from "../hooks/useToast";

interface BookingDialogProps {
  reservationItem: ReservationItem;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

type BookingStep = "date" | "time" | "options" | "confirm" | "result";

export function BookingDialog({
  reservationItem,
  isOpen,
  onClose,
  onConfirm,
}: BookingDialogProps) {
  const { botUUID } = useLiff();
  const { toast } = useToast();
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedTime, setSelectedTime] = useState<string>("");
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [step, setStep] = useState<BookingStep>("date");
  const [optionValues, setOptionValues] = useState<Record<string, string>>({});
  const [note, setNote] = useState<string>("");
  const [submissionStatus, setSubmissionStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const {
    data: availableTimes,
    isLoading,
    error,
  } = useGetAvailableTimesQuery(reservationItem.reservation_item_id, {
    skip: !isOpen,
    refetchOnMountOrArgChange: true, // 每次打開都重新獲取
  });

  const [createReservation, { isLoading: isCreating }] =
    useCreateNewReservationMutation();

  // 當可預約時間載入完成時，設定預設月份為第一個可預約日期的月份
  useEffect(() => {
    if (availableTimes && availableTimes.length > 0) {
      const firstAvailableDate = new Date(availableTimes[0].date);
      setCurrentMonth(
        new Date(
          firstAvailableDate.getFullYear(),
          firstAvailableDate.getMonth(),
          1
        )
      );
    }
  }, [availableTimes]);

  // 重置表單狀態
  const resetForm = () => {
    setSelectedDate("");
    setSelectedTime("");
    setStep("date");
    setOptionValues({});
    setNote("");
    setSubmissionStatus("idle");
    setErrorMessage("");
  };

  useEffect(() => {
    if (isOpen) {
      resetForm();
    }
  }, [isOpen]);

  // 處理預約提交
  const handleSubmitReservation = async () => {
    if (!botUUID || !selectedDate || !selectedTime) {
      return;
    }

    // 防止重複提交
    if (isCreating || submissionStatus !== "idle") {
      return;
    }

    try {
      setSubmissionStatus("idle");
      setErrorMessage("");

      // 構建選項值陣列
      const optionValuesArray: CreateReservationOptionValue[] = Object.entries(
        optionValues
      ).map(([optionId, value]) => ({
        option_id: optionId,
        value: value,
      }));

      // API 期望 start_time 為純時間格式 (HH:mm:ss)，而不是完整的日期時間
      // selectedTime 已經是 HH:mm:ss 格式，直接使用即可

      const reservationPayload = {
        bot_uuid: botUUID,
        reservation_item_id: reservationItem.reservation_item_id,
        reservation_date: selectedDate,
        start_time: selectedTime, // 直接使用時間格式，不包含日期
        payment_method: "cash" as const,
        payment_status: "unpaid" as const,
        option_values: optionValuesArray,
        note: note.trim() || undefined,
      };

      await createReservation(reservationPayload).unwrap();
      setSubmissionStatus("success");

      // 顯示成功 toast
      toast.success(`預約成功！服務：${reservationItem.reservation_name}`);

      // 延遲關閉對話框並調用成功回調
      setTimeout(() => {
        onConfirm();
        onClose();
      }, 2000);
    } catch (error) {
      console.error("預約失敗:", error);
      setSubmissionStatus("error");
      const errorMessage =
        error && typeof error === "object" && "data" in error
          ? (error.data as { message?: string })?.message || "預約失敗，請重試"
          : "預約失敗，請重試";

      setErrorMessage(errorMessage);

      // 顯示錯誤 toast
      toast.error(errorMessage);
    }
  };

  const handleDateSelect = (dateString: string) => {
    setSelectedDate(dateString);
    setSelectedTime(""); // 重置時間選擇
    setStep("time");
  };

  const handleTimeSelect = (timeString: string) => {
    setSelectedTime(timeString);
    // 如果有選項組需要填寫，進入選項步驟；否則進入確認步驟
    const hasActiveOptionGroups = reservationItem.option_groups.some(
      (group) => group.is_active && group.options.some((opt) => opt.is_active)
    );
    if (hasActiveOptionGroups) {
      setStep("options");
    } else {
      setStep("confirm");
    }
  };

  const handleOptionsNext = () => {
    // 檢查必填選項組是否都已填寫
    const requiredGroups = reservationItem.option_groups.filter(
      (group) => group.is_required && group.is_active
    );

    const missingRequired = requiredGroups.some((group) => {
      // 對於必填組，至少要選擇一個選項
      const hasSelectedOption = group.options.some(
        (opt) => opt.is_active && optionValues[opt.option_id]
      );
      return !hasSelectedOption;
    });

    if (missingRequired) {
      toast.error("請填寫所有必填選項");
      return;
    }

    setStep("confirm");
  };

  const handleOptionChange = (optionId: string, value: string) => {
    setOptionValues((prev) => ({
      ...prev,
      [optionId]: value,
    }));
  };

  // 返回上一步
  const handleBack = () => {
    switch (step) {
      case "time":
        setStep("date");
        setSelectedTime("");
        break;
      case "options":
        setStep("time");
        break;
      case "confirm": {
        const hasActiveOptionGroups = reservationItem.option_groups.some(
          (group) =>
            group.is_active && group.options.some((opt) => opt.is_active)
        );
        if (hasActiveOptionGroups) {
          setStep("options");
        } else {
          setStep("time");
        }
        break;
      }
      case "result":
        setStep("confirm");
        setSubmissionStatus("idle");
        setErrorMessage("");
        break;
    }
  };

  const formatTime = (timeString: string) => {
    return timeString.substring(0, 5);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("zh-TW", {
      month: "long",
      day: "numeric",
      weekday: "long",
    });
  };

  // 計算總價格
  const calculateTotalPrice = () => {
    let total = reservationItem.price;

    Object.entries(optionValues).forEach(([optionId, value]) => {
      // 在所有選項組中查找選項
      const option = reservationItem.option_groups
        .flatMap((group) => group.options)
        .find((opt) => opt.option_id === optionId);

      if (option && value) {
        // 根據選項值添加價格
        if (typeof value === "string" && !isNaN(Number(value))) {
          // 如果值是數字字符串，當作數量計算
          const quantity = parseInt(value) || 0;
          total += option.price * quantity;
        } else if (option.price > 0) {
          // 固定價格選項
          total += option.price;
        }
      }
    });

    return total;
  };

  // 創建可預約日期的 Set，用於快速查找
  const availableDatesSet = new Set(
    availableTimes?.map((slot) => slot.date) || []
  );

  // 獲取選中日期的時間段
  const selectedDateTimes =
    availableTimes?.find((slot) => slot.date === selectedDate)?.times || [];

  // 生成日曆網格
  const generateCalendarGrid = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    // 獲取當月第一天和最後一天
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // 獲取第一天是星期幾 (0=Sunday, 1=Monday, ...)
    const startingDayOfWeek = firstDay.getDay();

    const calendar = [];

    // 上個月的日期
    const prevMonth = month === 0 ? 11 : month - 1;
    const prevYear = month === 0 ? year - 1 : year;
    const prevMonthLastDay = new Date(prevYear, prevMonth + 1, 0).getDate();

    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
      const day = prevMonthLastDay - i;
      const date = new Date(prevYear, prevMonth, day);
      const dateString = formatDateString(date);
      calendar.push({
        date,
        dateString,
        isCurrentMonth: false,
        isAvailable: false,
      });
    }

    // 當月的日期
    for (let day = 1; day <= lastDay.getDate(); day++) {
      const date = new Date(year, month, day);
      const dateString = formatDateString(date);
      calendar.push({
        date,
        dateString,
        isCurrentMonth: true,
        isAvailable: availableDatesSet.has(dateString),
      });
    }

    // 下個月的日期（填滿6週）
    const totalCells = 42; // 6 rows × 7 days
    const remainingCells = totalCells - calendar.length;
    const nextMonth = month === 11 ? 0 : month + 1;
    const nextYear = month === 11 ? year + 1 : year;

    for (let day = 1; day <= remainingCells; day++) {
      const date = new Date(nextYear, nextMonth, day);
      const dateString = formatDateString(date);
      calendar.push({
        date,
        dateString,
        isCurrentMonth: false,
        isAvailable: false,
      });
    }

    return calendar;
  };

  // 統一的日期格式化函數，確保與 API 回應格式一致
  const formatDateString = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const goToPreviousMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1)
    );
  };

  const goToNextMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1)
    );
  };

  // 獲取步驟標題和圖標
  const getStepInfo = () => {
    switch (step) {
      case "date":
        return { title: "選擇預約日期", icon: Calendar };
      case "time":
        return { title: "選擇預約時間", icon: Clock };
      case "options":
        return { title: "預約選項", icon: Settings };
      case "confirm":
        return { title: "確認預約", icon: MessageSquare };
      case "result":
        return {
          title: submissionStatus === "success" ? "預約成功" : "預約失敗",
          icon: submissionStatus === "success" ? CheckCircle : XCircle,
        };
      default:
        return { title: "預約", icon: Calendar };
    }
  };

  if (!isOpen) return null;

  const stepInfo = getStepInfo();
  const StepIcon = stepInfo.icon;

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col h-screen">
      {/* 標題區域 - 固定在頂部 */}
      <div className="border-b bg-white p-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <StepIcon className="h-5 w-5" />
          <h2 className="text-lg font-semibold">{stepInfo.title}</h2>
        </div>
        <div className="text-sm text-muted-foreground mt-1">
          <p className="font-medium">{reservationItem.reservation_name}</p>
          <p>
            {reservationItem.duration_minutes}分鐘 • ${reservationItem.price}
          </p>
          {(step === "time" ||
            step === "options" ||
            step === "confirm" ||
            step === "result") &&
            selectedDate && (
              <p className="text-blue-600 mt-1">
                預約日期：{formatDate(selectedDate)}
              </p>
            )}
          {(step === "options" || step === "confirm" || step === "result") &&
            selectedTime && (
              <p className="text-blue-600">
                預約時間：{formatTime(selectedTime)}
              </p>
            )}
        </div>
      </div>

      {/* 內容區域 - 可滾動 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && (
          <div className="text-center py-4">
            <div className="text-muted-foreground">載入可預約時間中...</div>
          </div>
        )}

        {error && (
          <div className="text-center py-4">
            <div className="text-red-500">載入失敗，請重試</div>
          </div>
        )}

        {/* 日期選擇步驟 */}
        {!isLoading && !error && availableTimes && step === "date" && (
          <div className="flex flex-col items-center justify-center space-y-6 py-4">
            {/* 月份導航 */}
            <div className="flex items-center justify-center space-x-4">
              <Button variant="outline" size="sm" onClick={goToPreviousMonth}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <h3 className="font-medium text-center min-w-[120px]">
                {currentMonth.getFullYear()}年{currentMonth.getMonth() + 1}月
              </h3>
              <Button variant="outline" size="sm" onClick={goToNextMonth}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            <div className="w-full max-w-xs mx-auto">
              {/* 星期標題 */}
              <div className="grid grid-cols-7 gap-1 text-xs text-center font-medium text-muted-foreground mb-2">
                <div>日</div>
                <div>一</div>
                <div>二</div>
                <div>三</div>
                <div>四</div>
                <div>五</div>
                <div>六</div>
              </div>

              {/* 日曆網格 */}
              <div className="grid grid-cols-7 gap-1">
                {generateCalendarGrid().map((dayInfo, index) => (
                  <Button
                    key={index}
                    variant={
                      selectedDate === dayInfo.dateString ? "default" : "ghost"
                    }
                    size="sm"
                    className={`h-10 w-10 p-0 text-xs flex items-center justify-center relative ${
                      !dayInfo.isCurrentMonth
                        ? "text-muted-foreground/50"
                        : dayInfo.isAvailable
                        ? "hover:bg-blue-50 border-blue-200"
                        : "text-muted-foreground"
                    }`}
                    onClick={() =>
                      dayInfo.isAvailable && handleDateSelect(dayInfo.dateString)
                    }
                    disabled={!dayInfo.isAvailable}
                  >
                    {dayInfo.date.getDate()}
                    {dayInfo.isAvailable && (
                      <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2 w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                    )}
                  </Button>
                ))}
              </div>
            </div>

            {/* 說明文字 */}
            <div className="text-xs text-center text-muted-foreground">
              有藍點的日期表示可預約
            </div>
          </div>
        )}

        {/* 時間選擇步驟 */}
        {!isLoading &&
          !error &&
          step === "time" &&
          selectedDateTimes.length > 0 && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-2">
                {selectedDateTimes.map((timeSlot) => (
                  <Button
                    key={timeSlot.start_time}
                    variant={
                      selectedTime === timeSlot.start_time
                        ? "default"
                        : "outline"
                    }
                    size="sm"
                    className="h-10 text-xs flex items-center justify-center"
                    onClick={() => handleTimeSelect(timeSlot.start_time)}
                    disabled={timeSlot.available_capacity === 0}
                  >
                    <Clock className="h-3 w-3 mr-1" />
                    {formatTime(timeSlot.start_time)}
                  </Button>
                ))}
              </div>
            </div>
          )}

        {/* 選項設定步驟 */}
        {step === "options" &&
          reservationItem.option_groups &&
          reservationItem.option_groups.length > 0 && (
            <div className="space-y-6">
              {reservationItem.option_groups
                .filter((group) => group.is_active)
                .sort((a, b) => a.display_order - b.display_order)
                .map((group) => (
                  <div key={group.option_group_id} className="space-y-3">
                    <div className="border-b pb-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-base font-semibold">
                          {group.group_name}
                          {group.is_required && (
                            <span className="text-red-500 ml-1">*</span>
                          )}
                        </Label>
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded-full text-gray-600">
                          {group.selection_type === "single" ? "單選" : "多選"}
                        </span>
                      </div>
                      {group.group_description && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {group.group_description}
                        </p>
                      )}
                    </div>

                    <div className="space-y-3">
                      {group.options
                        .filter((option) => option.is_active)
                        .sort((a, b) => a.display_order - b.display_order)
                        .map((option) => (
                          <div key={option.option_id} className="space-y-2">
                            <div
                              className={`p-3 border-2 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                                optionValues[option.option_id] === "selected"
                                  ? "border-blue-500 bg-blue-50"
                                  : "border-gray-200 hover:border-gray-300"
                              }`}
                              onClick={() => {
                                if (group.selection_type === "single") {
                                  // 清除同組的其他選項
                                  const newValues = { ...optionValues };
                                  group.options.forEach((opt) => {
                                    delete newValues[opt.option_id];
                                  });
                                  newValues[option.option_id] = "selected";
                                  setOptionValues(newValues);
                                } else {
                                  // 多選邏輯
                                  if (
                                    optionValues[option.option_id] ===
                                    "selected"
                                  ) {
                                    handleOptionChange(option.option_id, "");
                                  } else {
                                    handleOptionChange(
                                      option.option_id,
                                      "selected"
                                    );
                                  }
                                }
                              }}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="font-medium text-sm">
                                    {option.option_name}
                                  </div>
                                  {option.option_description && (
                                    <div className="text-xs text-muted-foreground mt-1">
                                      {option.option_description}
                                    </div>
                                  )}
                                </div>
                                <div className="flex items-center space-x-2">
                                  {option.price > 0 && (
                                    <span className="text-sm font-medium text-blue-600">
                                      +${option.price}
                                    </span>
                                  )}
                                  {optionValues[option.option_id] ===
                                    "selected" && (
                                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                                      <svg
                                        className="w-3 h-3 text-white"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                      >
                                        <path
                                          fillRule="evenodd"
                                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                          clipRule="evenodd"
                                        />
                                      </svg>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}

              {/* 備註欄位 */}
              <div className="space-y-2 border-t pt-4">
                <Label className="text-sm font-medium">備註</Label>
                <Input
                  placeholder="請輸入備註（選填）"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
              </div>
            </div>
          )}

        {/* 確認步驟 */}
        {step === "confirm" && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              <h4 className="font-medium">預約詳情</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>服務項目：</span>
                  <span>{reservationItem.reservation_name}</span>
                </div>
                <div className="flex justify-between">
                  <span>預約日期：</span>
                  <span>{formatDate(selectedDate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>預約時間：</span>
                  <span>{formatTime(selectedTime)}</span>
                </div>
                <div className="flex justify-between">
                  <span>服務時長：</span>
                  <span>{reservationItem.duration_minutes}分鐘</span>
                </div>

                {/* 顯示選項 */}
                {Object.entries(optionValues).length > 0 && (
                  <>
                    <hr className="my-2" />
                    <div className="font-medium">預約選項：</div>
                    {reservationItem.option_groups
                      .filter((group) => group.is_active)
                      .map((group) => {
                        // 檢查這個組是否有選擇的選項
                        const groupOptions = group.options.filter(
                          (option) => optionValues[option.option_id]
                        );

                        if (groupOptions.length === 0) return null;

                        return (
                          <div key={group.option_group_id} className="ml-2">
                            <div className="font-medium text-sm text-gray-600">
                              {group.group_name}
                            </div>
                            {groupOptions.map((option) => {
                              const value = optionValues[option.option_id];
                              if (!value) return null;

                              return (
                                <div
                                  key={option.option_id}
                                  className="flex justify-between ml-4"
                                >
                                  <span>{option.option_name}</span>
                                  <span>
                                    {option.price > 0 && `+$${option.price}`}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        );
                      })}
                  </>
                )}

                {note && (
                  <>
                    <hr className="my-2" />
                    <div className="flex justify-between">
                      <span>備註：</span>
                      <span className="text-right max-w-[200px] break-words">
                        {note}
                      </span>
                    </div>
                  </>
                )}

                <hr className="my-2" />
                <div className="flex justify-between font-medium text-lg">
                  <span>總金額：</span>
                  <span className="text-blue-600">
                    ${calculateTotalPrice()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 結果步驟 */}
        {step === "result" && (
          <div className="text-center space-y-4">
            {submissionStatus === "success" && (
              <>
                <CheckCircle className="h-16 w-16 text-green-500 mx-auto" />
                <div>
                  <h3 className="text-lg font-medium text-green-700">
                    預約成功！
                  </h3>
                  <p className="text-sm text-muted-foreground mt-2">
                    您的預約已提交，我們會盡快為您安排。
                  </p>
                </div>
              </>
            )}

            {submissionStatus === "error" && (
              <>
                <XCircle className="h-16 w-16 text-red-500 mx-auto" />
                <div>
                  <h3 className="text-lg font-medium text-red-700">預約失敗</h3>
                  <p className="text-sm text-red-600 mt-2">{errorMessage}</p>
                </div>
              </>
            )}
          </div>
        )}

        {!isLoading &&
          !error &&
          availableTimes &&
          availableTimes.length === 0 && (
            <div className="text-center py-4">
              <div className="text-muted-foreground">暫無可預約時間</div>
            </div>
          )}

        {!isLoading &&
          !error &&
          availableTimes &&
          availableTimes.length === 0 && (
            <div className="text-center py-4">
              <div className="text-muted-foreground">暫無可預約時間</div>
            </div>
          )}
      </div>

      {/* 操作按鈕 - 固定在底部 */}
      <div className="border-t bg-white p-4 pb-8 flex-shrink-0">
        <div className="flex gap-2">
          {step === "date" && (
            <Button variant="outline" onClick={onClose} className="w-full">
              取消
            </Button>
          )}

          {(step === "time" || step === "options" || step === "confirm") && (
            <>
              <Button variant="outline" onClick={handleBack} className="flex-1">
                上一步
              </Button>
              {step === "time" && (
                <Button
                  onClick={() => handleTimeSelect(selectedTime)}
                  disabled={!selectedTime}
                  className="flex-1"
                >
                  下一步
                </Button>
              )}
              {step === "options" && (
                <Button onClick={handleOptionsNext} className="flex-1">
                  下一步
                </Button>
              )}
              {step === "confirm" && (
                <Button
                  onClick={handleSubmitReservation}
                  disabled={isCreating || submissionStatus !== "idle"}
                  className="flex-1"
                >
                  {isCreating ? "提交中..." : "確認預約"}
                </Button>
              )}
            </>
          )}

          {step === "result" && submissionStatus === "error" && (
            <>
              <Button variant="outline" onClick={handleBack} className="flex-1">
                重試
              </Button>
              <Button variant="outline" onClick={onClose} className="flex-1">
                關閉
              </Button>
            </>
          )}

          {step === "result" && submissionStatus === "success" && (
            <div className="w-full text-center text-sm text-muted-foreground">
              自動關閉中...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
