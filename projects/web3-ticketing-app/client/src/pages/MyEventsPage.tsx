import { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Grid,
  CircularProgress,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import { formatEther } from "ethers";
import { useEventContract } from "@/hooks/useEventContract";
import { useWallet } from "@/context/WalletContext";
import { useToast } from "@/context/ToastProvider";
import { useNavigate } from "react-router";
import { useMediaQuery } from "@mui/material";

interface EventData {
  eventId: number;
  name: string;
  ticketPrice: string;
  totalTickets: number;
  ticketsSold: number;
  active: boolean;
  revenue: bigint;
  isSoulBound: boolean;
}

export default function MyEvents() {
  const contract = useEventContract();
  const { account: userAddress } = useWallet();
  const toast = useToast();
  const navigate = useNavigate();

  const [events, setEvents] = useState<EventData[]>([]);
  const [loading, setLoading] = useState(true);
  const [ticketDialogOpen, setTicketDialogOpen] = useState(false);
  const [tickets, setTickets] = useState<
    { id: number; uri: string; owner: string }[]
  >([]);

  const fetchMyEvents = async () => {
    if (!contract || !userAddress) return;
    try {
      setLoading(true);
      const eventIdCounter = await contract.eventIdCounter();
      const eventList: EventData[] = [];

      for (let id = 1; id < eventIdCounter; id++) {
        const ev = await contract.events(id);
        if (ev.organizer.toLowerCase() !== userAddress.toLowerCase()) continue;

        const revenue: bigint = await contract.getEventRevenue(id);
        eventList.push({
          eventId: id,
          name: ev.name,
          ticketPrice: `${formatEther(ev.ticketPrice)} ETH`,
          totalTickets: Number(ev.totalTickets),
          ticketsSold: Number(ev.ticketsSold),
          active: ev.active,
          revenue,
          isSoulBound: ev.isSoulBound,
        });
      }

      setEvents(eventList);
    } catch (err) {
      console.error("Failed to load your events", err);
      toast.error("Failed to load your events");
    } finally {
      setLoading(false);
    }
  };

  const handleViewTickets = async (eventId: number) => {
    if (!contract || !userAddress) return;
    try {
      const ticketIds: number[] = await contract.getEventTicketIds(eventId);
      const holders: string[] = await contract.getEventTicketHolders(eventId);

      const ticketInfo = await Promise.all(
        ticketIds.map(async (id) => {
          const uri = await contract.tokenURI(id);
          return { id, uri };
        })
      );

      const combined = ticketInfo.map((t, index) => ({
        ...t,
        owner: holders[index],
      }));

      setTickets(combined);
      setTicketDialogOpen(true);
    } catch (err) {
      toast.error("無法取得票券資訊");
      console.error("getEventTicketIds error:", err);
    }
  };

  const handleWithdrawRevenue = async (eventId: number) => {
    if (!contract) return;
    try {
      const tx = await contract.withdrawEventRevenue(eventId);
      await tx.wait();
      toast.success("成功提領收益！");
      await fetchMyEvents(); // 更新收益狀態
    } catch (err: any) {
      console.error("Withdraw revenue failed", err);
      const msg = err?.message?.toLowerCase() ?? "";
      if (msg.includes("no revenue")) {
        toast.error("⚠️ 目前沒有可提領的收益");
      } else {
        toast.error("提領收益失敗");
      }
    }
  };

  const handleToggleActive = async (eventId: number, newState: boolean) => {
    if (!contract) return;
    try {
      const tx = await contract.setEventActive(eventId, newState);
      await tx.wait();
      toast.success(`🎯 活動已${newState ? "開啟" : "關閉"}`);
      await fetchMyEvents();
    } catch (err) {
      console.error("Toggle event active failed", err);
      toast.error("無法切換活動狀態");
    }
  };

  useEffect(() => {
    if (contract && userAddress) fetchMyEvents();
  }, [contract, userAddress]);

  return (
    <Box p={4}>
      <Typography variant="h4" mb={2}>
        我的活動
      </Typography>

      {!userAddress ? (
        <Typography>請連接錢包以檢視你的活動</Typography>
      ) : loading ? (
        <CircularProgress />
      ) : events.length === 0 ? (
        <Typography>你尚未創建任何活動</Typography>
      ) : (
        <Grid container spacing={2}>
          {events.map((ev) => (
            <Grid size={{ xs: 12, md: 6 }} key={ev.eventId}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6">
                  #{ev.eventId} - {ev.name}
                </Typography>
                <Typography>票價：{ev.ticketPrice}</Typography>
                <Typography>
                  餘票：{ev.totalTickets - ev.ticketsSold} / {ev.totalTickets}
                </Typography>
                <Typography>
                  狀態：{ev.active ? "開放中" : "已關閉"}
                  {ev.isSoulBound && "（靈魂綁定）"}
                </Typography>
                <Typography>收益：{formatEther(ev.revenue)} ETH</Typography>
                <Grid container spacing={1} mt={2}>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Button
                      fullWidth
                      variant="outlined"
                      onClick={() => handleViewTickets(ev.eventId)}
                    >
                      票券清單
                    </Button>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Button
                      fullWidth
                      variant="outlined"
                      color="warning"
                      onClick={() => handleToggleActive(ev.eventId, !ev.active)}
                    >
                      {ev.active ? "關閉活動" : "開啟活動"}
                    </Button>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="primary"
                      onClick={() =>
                        navigate(`/check-in?eventId=${ev.eventId}`)
                      }
                    >
                      驗票
                    </Button>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 3 }}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="success"
                      disabled={ev.revenue <= 0}
                      onClick={() => handleWithdrawRevenue(ev.eventId)}
                    >
                      提領收益
                    </Button>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          ))}
        </Grid>
      )}

      {/* 票券 Dialog */}
      <Dialog
        open={ticketDialogOpen}
        onClose={() => setTicketDialogOpen(false)}
        fullScreen={useMediaQuery((theme: any) => theme.breakpoints.down("sm"))}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>票券清單（含持有者）</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            {tickets.map((t) => (
              <Grid size={{ xs: 12, sm: 6 }} key={t.id}>
                <Box
                  p={2}
                  border={1}
                  borderColor="grey.300"
                  borderRadius={2}
                  sx={{ wordBreak: "break-word" }}
                >
                  <Typography fontWeight="bold">
                    🎫 Ticket ID: {t.id}
                  </Typography>
                  <Typography
                    noWrap
                    sx={{ textOverflow: "ellipsis", overflow: "hidden" }}
                  >
                    🔗 URI:
                    <a
                      href={t.uri}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ marginLeft: 4 }}
                    >
                      {t.uri}
                    </a>
                  </Typography>
                  <Typography
                    noWrap
                    sx={{ textOverflow: "ellipsis", overflow: "hidden" }}
                  >
                    👤 擁有者: {t.owner}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTicketDialogOpen(false)}>關閉</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
