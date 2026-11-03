import { useState } from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CircularProgress,
} from "@mui/material";
import { useEventContract } from "@/hooks/useEventContract";
import { Scanner } from "@yudiel/react-qr-scanner";
import { useSearchParams, useNavigate } from "react-router";
import { useToast } from "@/context/ToastProvider";

export default function CheckInPage() {
  const contract = useEventContract();
  const navigate = useNavigate();
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const eventIdParam = searchParams.get("eventId");
  const expectedEventId = eventIdParam ? parseInt(eventIdParam) : null;
  const [ticketId, setTicketId] = useState("");
  const [message, setMessage] = useState("");
  const [signature, setSignature] = useState("");
  const [timestamp, setTimestamp] = useState("");
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [scanning, setScanning] = useState(false);

  const [ticketInfo, setTicketInfo] = useState<{
    eventName: string;
    checkedInAt: number;
    imageUrl: string;
  } | null>(null);

  if (!expectedEventId) {
    navigate("/");
  }

  const handleScan = async (data: string | null) => {
    if (!data) return;

    try {
      const payload = JSON.parse(data);
      setTicketId(String(payload.ticketId));
      setMessage(payload.message);
      setSignature(payload.signature);
      setTimestamp(String(payload.timestamp));
      setScanning(false);
      toast.success("📷 掃描成功，請確認後點擊驗票");
    } catch (err) {
      toast.error("無法解析 QR Code 資料");
    }
  };

  const handleSearch = async () => {
    if (!contract || !ticketId) return;
    setLoading(true);
    setTicketInfo(null);

    try {
      const [eventId, checkedInAt, tokenUri] = await Promise.all([
        contract.ticketToEvent(ticketId),
        contract.getCheckInTimestamp(ticketId),
        contract.tokenURI(ticketId),
      ]);

      const eventData = await contract.events(eventId);
      const imageUrl = tokenUri.replace("ipfs://", "https://ipfs.io/ipfs/");

      setTicketInfo({
        eventName: eventData.name,
        checkedInAt: Number(checkedInAt),
        imageUrl,
      });
    } catch (err) {
      console.error("查票券失敗", err);
      toast.error("查無票券或輸入錯誤");
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async () => {
    if (!contract || !ticketId || !message || !signature || !timestamp) {
      toast.error("請填寫完整資訊");
      return;
    }

    try {
      setChecking(true);

      const tx = await contract.checkInByOrganizer(
        expectedEventId, // 新增
        ticketId,
        message,
        signature,
        timestamp
      );

      await tx.wait();
      setTicketInfo((prev) =>
        prev ? { ...prev, checkedInAt: Math.floor(Date.now() / 1000) } : prev
      );
      toast.success("驗票成功！");
    } catch (err) {
      console.error("驗票失敗", err);
      toast.error("驗票失敗，請確認簽章與訊息格式正確，且你是主辦方");
    } finally {
      setChecking(false);
    }
  };

  return (
    <Box p={4}>
      <Typography variant="h4" textAlign="center" mb={4}>
        驗票入口（主辦方專用）
      </Typography>

      <Box
        display="flex"
        flexDirection={{ xs: "column", md: "row" }}
        justifyContent="center"
        alignItems="flex-start"
        gap={4}
        flexWrap="wrap"
      >
        {/* 左側：掃描區 */}
        <Box maxWidth={500} width="100%">
          <Button
            variant="outlined"
            fullWidth
            onClick={() => setScanning((v) => !v)}
          >
            {scanning ? "停止掃描" : "掃描 QR Code"}
          </Button>

          {scanning && (
            <Box mt={2}>
              <Scanner
                onScan={(result) => handleScan(result[0].rawValue)}
                onError={(error) => {
                  console.error("QR 掃描錯誤", error);
                  toast.error("⚠️ 無法啟用鏡頭或讀取失敗，請改用手動輸入");
                }}
                constraints={{ facingMode: "environment" }}
                styles={{ container: { width: "100%", height: 300 } }}
              />
            </Box>
          )}

          {/* 查詢按鈕（只有掃描成功後才顯示） */}
          {ticketId && message && signature && timestamp && (
            <Button
              variant="contained"
              color="primary"
              onClick={handleSearch}
              disabled={loading}
              fullWidth
              sx={{ mt: 2 }}
            >
              {loading ? "查詢中..." : "查詢票券資訊"}
            </Button>
          )}
        </Box>

        {/* 右側：票券資訊卡片 */}
        {ticketInfo && (
          <Card sx={{ width: "100%", maxWidth: 500 }}>
            <CardContent>
              <Typography variant="h6">{ticketInfo.eventName}</Typography>
              <Typography>
                狀態:{" "}
                {ticketInfo.checkedInAt
                  ? `已驗票：${new Date(
                      ticketInfo.checkedInAt * 1000
                    ).toLocaleString()}`
                  : "尚未驗票"}
              </Typography>
              <Box mt={2} display="flex" justifyContent="center">
                <img
                  src={ticketInfo.imageUrl}
                  alt="Ticket"
                  style={{ width: "100%", maxWidth: 300, borderRadius: 8 }}
                />
              </Box>
              {!ticketInfo.checkedInAt && (
                <Box mt={2} textAlign="center">
                  <Button
                    variant="contained"
                    color="success"
                    onClick={handleCheckIn}
                    disabled={checking}
                  >
                    {checking ? <CircularProgress size={20} /> : "驗票"}
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        )}
      </Box>
    </Box>
  );
}
