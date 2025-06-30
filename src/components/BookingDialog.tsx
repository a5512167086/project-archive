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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useGetAvailableTimesQuery,
  useCreateNewReservationMutation,
  type ReservationItem,
  type CreateReservationOptionValue,
} from "../store/api/reservationApi";
import { useLiff } from "../hooks/useLiff";

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

      // 延遲關閉對話框並調用成功回調
      setTimeout(() => {
        onConfirm();
        onClose();
      }, 2000);
    } catch (error) {
      console.error("預約失敗:", error);
      setSubmissionStatus("error");
      setErrorMessage(
        error && typeof error === "object" && "data" in error
          ? (error.data as { message?: string })?.message || "預約失敗，請重試"
          : "預約失敗，請重試"
      );
    }
  };

  const handleDateSelect = (dateString: string) => {
    setSelectedDate(dateString);
    setSelectedTime(""); // 重置時間選擇
    setStep("time");
  };

  const handleTimeSelect = (timeString: string) => {
    setSelectedTime(timeString);
    // 如果有選項需要填寫，進入選項步驟；否則進入確認步驟
    if (reservationItem.options && reservationItem.options.length > 0) {
      setStep("options");
    } else {
      setStep("confirm");
    }
  };

  const handleOptionsNext = () => {
    // 檢查必填選項是否都已填寫
    const requiredOptions = reservationItem.options.filter(
      (opt) => opt.is_required && opt.is_active
    );
    const missingRequired = requiredOptions.some(
      (opt) => !optionValues[opt.option_id]
    );

    if (missingRequired) {
      alert("請填寫所有必填選項");
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
      case "confirm":
        if (reservationItem.options && reservationItem.options.length > 0) {
          setStep("options");
        } else {
          setStep("time");
        }
        break;
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
      const option = reservationItem.options.find(
        (opt) => opt.option_id === optionId
      );
      if (option && value) {
        if (option.type === "number") {
          const quantity = parseInt(value) || 0;
          total += option.price * quantity;
        } else if (option.price > 0) {
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md max-h-[80vh] overflow-y-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <StepIcon className="h-5 w-5" />
            {stepInfo.title}
          </CardTitle>
          <div className="text-sm text-muted-foreground">
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
        </CardHeader>
        <CardContent className="space-y-4">
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
            <div className="space-y-4">
              {/* 月份導航 */}
              <div className="flex items-center justify-center">
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

              {/* 星期標題 */}
              <div className="grid grid-cols-7 gap-1 text-xs text-center font-medium text-muted-foreground">
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
                    className={`h-8 w-8 p-0 text-xs flex items-center justify-center relative ${
                      !dayInfo.isCurrentMonth
                        ? "text-muted-foreground/50"
                        : dayInfo.isAvailable
                        ? "hover:bg-blue-50 border-blue-200"
                        : "text-muted-foreground"
                    }`}
                    onClick={() =>
                      dayInfo.isAvailable &&
                      handleDateSelect(dayInfo.dateString)
                    }
                    disabled={!dayInfo.isAvailable}
                  >
                    {dayInfo.date.getDate()}
                    {dayInfo.isAvailable && (
                      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-500 rounded-full"></div>
                    )}
                  </Button>
                ))}
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
                      className="h-10 text-xs flex flex-col items-center justify-center"
                      onClick={() => handleTimeSelect(timeSlot.start_time)}
                      disabled={timeSlot.available_capacity === 0}
                    >
                      <div className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatTime(timeSlot.start_time)}
                      </div>
                      {timeSlot.available_capacity < 2 &&
                        timeSlot.available_capacity > 0 && (
                          <span className="text-orange-500 text-xs">
                            剩{timeSlot.available_capacity}位
                          </span>
                        )}
                    </Button>
                  ))}
                </div>
              </div>
            )}

          {/* 選項設定步驟 */}
          {step === "options" &&
            reservationItem.options &&
            reservationItem.options.length > 0 && (
              <div className="space-y-4">
                {reservationItem.options
                  .filter((option) => option.is_active)
                  .map((option) => (
                    <div key={option.option_id} className="space-y-2">
                      <Label className="text-sm font-medium">
                        {option.option_name}
                        {option.is_required && (
                          <span className="text-red-500 ml-1">*</span>
                        )}
                        {option.price > 0 && (
                          <span className="text-muted-foreground ml-2">
                            (+${option.price}
                            {option.type === "number" ? "/個" : ""})
                          </span>
                        )}
                      </Label>
                      {option.option_description && (
                        <p className="text-xs text-muted-foreground">
                          {option.option_description}
                        </p>
                      )}

                      {option.type === "text" && (
                        <Input
                          placeholder={`請輸入${option.option_name}`}
                          value={optionValues[option.option_id] || ""}
                          onChange={(e) =>
                            handleOptionChange(option.option_id, e.target.value)
                          }
                        />
                      )}

                      {option.type === "number" && (
                        <Input
                          type="number"
                          min="0"
                          placeholder="請輸入數量"
                          value={optionValues[option.option_id] || ""}
                          onChange={(e) =>
                            handleOptionChange(option.option_id, e.target.value)
                          }
                        />
                      )}

                      {option.type === "select" && (
                        <Select
                          value={optionValues[option.option_id] || ""}
                          onValueChange={(value) =>
                            handleOptionChange(option.option_id, value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue
                              placeholder={`請選擇${option.option_name}`}
                            />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="是">是</SelectItem>
                            <SelectItem value="否">否</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    </div>
                  ))}

                {/* 備註欄位 */}
                <div className="space-y-2">
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
                      {Object.entries(optionValues).map(([optionId, value]) => {
                        const option = reservationItem.options.find(
                          (opt) => opt.option_id === optionId
                        );
                        if (!option || !value) return null;
                        return (
                          <div key={optionId} className="flex justify-between">
                            <span>{option.option_name}：</span>
                            <span>
                              {value}
                              {option.price > 0 &&
                                ` (+$${
                                  option.type === "number"
                                    ? option.price * (parseInt(value) || 0)
                                    : option.price
                                })`}
                            </span>
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
                    <h3 className="text-lg font-medium text-red-700">
                      預約失敗
                    </h3>
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

          {/* 操作按鈕 */}
          <div className="flex gap-2 pt-4">
            {step === "date" && (
              <Button variant="outline" onClick={onClose} className="w-full">
                取消
              </Button>
            )}

            {(step === "time" || step === "options" || step === "confirm") && (
              <>
                <Button
                  variant="outline"
                  onClick={handleBack}
                  className="flex-1"
                >
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
                <Button
                  variant="outline"
                  onClick={handleBack}
                  className="flex-1"
                >
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
        </CardContent>
      </Card>
    </div>
  );
}
