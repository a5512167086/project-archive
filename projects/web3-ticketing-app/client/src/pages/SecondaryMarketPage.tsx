import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  CircularProgress,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useEventContract } from "@/hooks/useEventContract";
import { useWallet } from "@/context/WalletContext";
import { useToast } from "@/context/ToastProvider";
import { formatEther } from "ethers";

interface ListingInfo {
  ticketId: number;
  seller: string;
  price: bigint;
  active: boolean;
  eventName: string;
}

export default function SecondaryMarketPage() {
  const contract = useEventContract();
  const { account } = useWallet();
  const toast = useToast();

  const [listings, setListings] = useState<ListingInfo[]>([]);
  const [filtered, setFiltered] = useState<ListingInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [filterEvent, setFilterEvent] = useState("全部");

  const formatAddress = (addr: string) =>
    `${addr.slice(0, 6)}...${addr.slice(-4)}`;

  const fetchListings = async () => {
    if (!contract) return;
    setLoading(true);

    const results: ListingInfo[] = [];

    try {
      const total = await contract.ticketIdCounter();

      for (let ticketId = 1; ticketId < total; ticketId++) {
        const listing = await contract.listings(ticketId);
        if (listing.active) {
          const eventId = await contract.ticketToEvent(ticketId);
          const eventData = await contract.events(eventId);

          results.push({
            ticketId,
            seller: listing.seller,
            price: listing.price,
            active: listing.active,
            eventName: eventData.name,
          });
        }
      }

      setListings(results);
      setFiltered(results);
    } catch (error) {
      toast.error("載入失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleBuy = async (ticketId: number, price: bigint) => {
    if (!contract || !account) return;

    try {
      setProcessingId(ticketId);
      const tx = await contract.buyListedTicket(ticketId, { value: price });
      await tx.wait();
      toast.success("購票成功");
      fetchListings();
    } catch (err: any) {
      if (err.message?.includes("user rejected")) {
        toast.error("你取消了交易簽名");
      } else {
        toast.error("購買失敗");
      }
    } finally {
      setProcessingId(null);
    }
  };

  const handleCancel = async (ticketId: number) => {
    if (!contract || !account) return;

    try {
      setProcessingId(ticketId);
      const tx = await contract.cancelListing(ticketId);
      await tx.wait();
      toast.success("成功取消上架");
      fetchListings();
    } catch (err: any) {
      if (err.message?.includes("user rejected")) {
        toast.error("你取消了交易簽名");
      } else {
        toast.error("取消失敗");
      }
    } finally {
      setProcessingId(null);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [contract]);

  const uniqueEventNames = [
    "全部",
    ...new Set(listings.map((l) => l.eventName)),
  ];

  useEffect(() => {
    if (filterEvent === "全部") {
      setFiltered(listings);
    } else {
      setFiltered(listings.filter((l) => l.eventName === filterEvent));
    }
  }, [filterEvent, listings]);

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        二級市場票券交易
      </Typography>

      <Box mt={2} mb={3}>
        <FormControl size="small">
          <InputLabel id="filter-label">篩選活動</InputLabel>
          <Select
            labelId="filter-label"
            value={filterEvent}
            label="篩選活動"
            onChange={(e) => setFilterEvent(e.target.value)}
          >
            {uniqueEventNames.map((name) => (
              <MenuItem key={name} value={name}>
                {name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : filtered.length === 0 ? (
        <Typography>目前沒有符合條件的票券</Typography>
      ) : (
        <Grid container spacing={2}>
          {filtered.map((listing) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={listing.ticketId}>
              <Card>
                <CardContent>
                  <Typography variant="h6">票券 #{listing.ticketId}</Typography>
                  <Typography>
                    售價: {formatEther(listing.price)} ETH
                  </Typography>
                  <Typography noWrap>
                    賣家: {formatAddress(listing.seller)}
                  </Typography>
                  <Typography>活動名稱: {listing.eventName}</Typography>

                  {account?.toLowerCase() === listing.seller.toLowerCase() ? (
                    <Button
                      variant="outlined"
                      color="secondary"
                      onClick={() => handleCancel(listing.ticketId)}
                      disabled={processingId === listing.ticketId}
                      sx={{ mt: 2 }}
                    >
                      {processingId === listing.ticketId
                        ? "取消中..."
                        : "取消上架"}
                    </Button>
                  ) : (
                    <Button
                      variant="contained"
                      onClick={() => handleBuy(listing.ticketId, listing.price)}
                      disabled={processingId === listing.ticketId}
                      sx={{ mt: 2 }}
                    >
                      {processingId === listing.ticketId
                        ? "購買中..."
                        : "立即購買"}
                    </Button>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
