import { useEffect, useState } from "react";
import { formatEther, parseEther } from "ethers";
import {
  Box,
  Typography,
  Grid,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Paper,
  Checkbox,
  FormControlLabel,
  Select,
  MenuItem,
} from "@mui/material";
import { useEventContract } from "@/hooks/useEventContract";
import { useToast } from "@/context/ToastProvider";
import { generateTicketImageBlobJS } from "@/utils/index";
import { uploadToPinata } from "@/utils/nftStorage";
import { useWallet } from "@/context/WalletContext";

interface EventData {
  eventId: number;
  name: string;
  ticketPrice: string;
  ticketPriceRaw: bigint;
  totalTickets: number;
  ticketsSold: number;
  active: boolean;
  isOwner: boolean;
  isSoulBound: boolean;
}

export default function EventList() {
  const { account: userAddress } = useWallet();
  const contract = useEventContract();
  const toast = useToast();

  const [events, setEvents] = useState<EventData[]>([]);
  const [loading, setLoading] = useState(true);
  const [buyingId, setBuyingId] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newEventName, setNewEventName] = useState("");
  const [newTicketPrice, setNewTicketPrice] = useState("");
  const [newTicketCount, setNewTicketCount] = useState("");
  const [newIsSoulBound, setNewIsSoulBound] = useState(false);
  const [creating, setCreating] = useState(false);
  const [filter, setFilter] = useState("全部");

  const fetchEvents = async () => {
    if (!contract || !userAddress) return;
    try {
      setLoading(true);
      const eventIdCounter = await contract.eventIdCounter();
      const promises = [];
      for (let id = 1; id < eventIdCounter; id++) {
        promises.push(contract.events(id));
      }
      const rawEvents = await Promise.all(promises);
      const formatted = rawEvents.map((ev: any, index) => ({
        eventId: index + 1,
        name: ev.name,
        ticketPrice: `${formatEther(ev.ticketPrice)} ETH`,
        ticketPriceRaw: ev.ticketPrice,
        totalTickets: Number(ev.totalTickets),
        ticketsSold: Number(ev.ticketsSold),
        active: ev.active,
        isOwner: ev.organizer.toLowerCase() === userAddress.toLowerCase(),
        isSoulBound: ev.isSoulBound,
      }));

      setEvents(formatted);
    } catch (err) {
      console.error("Failed to load events", err);
      toast.error("Failed to load events!");
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = events.filter((event) => {
    if (filter === "全部") return true;
    if (filter === "可購買") {
      return (
        event.active &&
        !event.isOwner &&
        !event.isSoulBound &&
        event.ticketsSold < event.totalTickets
      );
    }
    if (filter === "SBT") {
      return event.isSoulBound;
    }
    return true;
  });

  useEffect(() => {
    if (contract && userAddress) fetchEvents();
  }, [contract, userAddress]);

  const handleBuy = async (
    eventId: number,
    price: bigint,
    eventName: string
  ) => {
    if (!contract || !userAddress) return;
    try {
      setBuyingId(eventId);
      const ticketId: bigint = await contract.ticketIdCounter();

      const blob = await generateTicketImageBlobJS({
        eventId,
        eventName,
      });

      const uri = await uploadToPinata({
        file: blob,
        fileName: `event-${eventId}-ticket-${ticketId}.png`,
      });

      const tx = await contract.mintTicket(eventId, uri, {
        value: price,
      });

      await tx.wait();
      toast.success("✅ Ticket minted successfully!");
      await fetchEvents();
    } catch (err: any) {
      const rawMsg = err?.message?.toLowerCase?.() || "";
      if (rawMsg.includes("user denied") || rawMsg.includes("rejected")) {
        toast.error("你取消了交易簽名");
      } else if (rawMsg.includes("insufficient funds")) {
        toast.error("錢包餘額不足");
      } else {
        toast.error("Ticket mint failed，請稍後再試");
      }
    } finally {
      setBuyingId(null);
    }
  };

  const handleCreateEvent = async () => {
    if (!contract) return;
    try {
      setCreating(true);

      const ticketCount = Number(newTicketCount);
      const price = parseEther(newTicketPrice);

      const tx = await contract.createEvent(
        newEventName,
        price,
        ticketCount,
        newIsSoulBound
      );

      await tx.wait();
      toast.success("✅ Event created successfully!");
      setDialogOpen(false);
      setNewEventName("");
      setNewTicketPrice("");
      setNewTicketCount("");
      await fetchEvents();
    } catch (err: any) {
      console.error("Event creation failed", err);
      toast.error("Event creation failed: " + err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Box p={4}>
      <Box
        component={Paper}
        elevation={3}
        sx={{ bgcolor: "background.paper", p: 4, borderRadius: 2 }}
      >
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={3}
          flexWrap="wrap"
          gap={2}
        >
          <Typography variant="h4">所有活動</Typography>
          <Box display="flex" gap={2} alignItems="center">
            <Select
              size="small"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <MenuItem value="全部">全部</MenuItem>
              <MenuItem value="可購買">可購買</MenuItem>
              <MenuItem value="SBT">SBT</MenuItem>
            </Select>
            <Button variant="contained" onClick={() => setDialogOpen(true)}>
              Create Event
            </Button>
          </Box>
        </Box>

        <Dialog
          open={dialogOpen}
          onClose={(_, reason) => {
            if (reason !== "backdropClick") {
              setDialogOpen(false);
            }
          }}
          fullWidth
        >
          <DialogTitle>Create New Event</DialogTitle>
          <DialogContent>
            <TextField
              margin="dense"
              label="Event Name"
              fullWidth
              value={newEventName}
              onChange={(e) => setNewEventName(e.target.value)}
            />
            <TextField
              margin="dense"
              label="Ticket Price (ETH)"
              fullWidth
              type="number"
              value={newTicketPrice}
              onChange={(e) => setNewTicketPrice(e.target.value)}
            />
            <TextField
              margin="dense"
              label="Total Tickets"
              fullWidth
              type="number"
              value={newTicketCount}
              onChange={(e) => setNewTicketCount(e.target.value)}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={newIsSoulBound}
                  onChange={(e) => setNewIsSoulBound(e.target.checked)}
                />
              }
              label="Make tickets Soul Bound (non-transferable)"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)} disabled={creating}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateEvent}
              disabled={
                creating || !newEventName || !newTicketPrice || !newTicketCount
              }
            >
              {creating ? <CircularProgress size={20} /> : "Create"}
            </Button>
          </DialogActions>
        </Dialog>

        {!userAddress ? (
          <Typography>Please connect your wallet to view events.</Typography>
        ) : loading ? (
          <CircularProgress />
        ) : filteredEvents.length === 0 ? (
          <Typography>No events found.</Typography>
        ) : (
          <Grid container spacing={2} mt={2}>
            {filteredEvents.map((event) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={event.eventId}>
                <Box
                  p={2}
                  border={1}
                  borderColor="grey.300"
                  borderRadius={2}
                  display="flex"
                  flexDirection="column"
                  gap={1}
                  sx={{ bgcolor: "background.default", height: "100%" }}
                >
                  <Typography variant="h6">
                    {event.name} {event.isOwner && "(Owner)"}
                  </Typography>
                  <Typography>Price: {event.ticketPrice}</Typography>
                  <Typography>
                    Remaining Tickets: {event.totalTickets - event.ticketsSold}{" "}
                    / {event.totalTickets}
                  </Typography>
                  <Typography>
                    Status: {event.active ? "Open" : "Closed"}
                    {event.isSoulBound && " (Soul Bound)"}
                  </Typography>
                  {event.active && (
                    <Button
                      variant="contained"
                      color="primary"
                      disabled={
                        buyingId === event.eventId ||
                        event.isOwner ||
                        event.ticketsSold >= event.totalTickets
                      }
                      onClick={() =>
                        handleBuy(
                          event.eventId,
                          event.ticketPriceRaw,
                          event.name
                        )
                      }
                      startIcon={
                        buyingId === event.eventId ? (
                          <CircularProgress size={18} color="inherit" />
                        ) : null
                      }
                    >
                      {event.ticketsSold >= event.totalTickets
                        ? "Tickets Sold Out"
                        : event.isOwner
                        ? "Owner Can't Buy Ticket"
                        : buyingId === event.eventId
                        ? "Purchasing..."
                        : "Buy Ticket"}
                    </Button>
                  )}
                </Box>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Box>
  );
}
