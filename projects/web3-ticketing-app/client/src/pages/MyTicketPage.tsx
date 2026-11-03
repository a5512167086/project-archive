import { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Button,
} from "@mui/material";
import { useWallet } from "@/context/WalletContext";
import { useEventContract } from "@/hooks/useEventContract";
import { QRCodeCanvas } from "qrcode.react";
import { useToast } from "@/context/ToastProvider";

interface TicketData {
  ticketId: number;
  eventId: number;
  eventName: string;
  checkedInAt: number;
  imageUrl: string;
  isListed: boolean;
  isSoulBound: boolean;
}

export default function MyTickets() {
  const toast = useToast();
  const { account, signer } = useWallet();
  const contract = useEventContract();
  const [listingPrices, setListingPrices] = useState<Record<number, string>>(
    {}
  );
  const [listingLoading, setListingLoading] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [signatures, setSignatures] = useState<
    Record<
      number,
      {
        message: string;
        signature: string;
        timestamp: number;
      }
    >
  >({});

  const handleListTicket = async (ticketId: number) => {
    if (!contract || !listingPrices[ticketId]) return;

    try {
      setListingLoading(ticketId);
      const priceInWei = BigInt(
        Number(listingPrices[ticketId]) * 1e18
      ).toString();

      const tx = await contract.listTicket(ticketId, priceInWei);
      await tx.wait();

      toast.success("上架成功！");
      setListingPrices((prev) => ({ ...prev, [ticketId]: "" }));

      // ✅ 更新 UI 狀態為已上架
      setTickets((prev) =>
        prev.map((t) =>
          t.ticketId === ticketId ? { ...t, isListed: true } : t
        )
      );
    } catch (err: any) {
      if (err.message?.includes("user rejected")) {
        toast.error("你取消了交易簽章");
      } else {
        toast.error("上架失敗");
      }
    } finally {
      setListingLoading(null);
    }
  };

  const handleCancelListing = async (ticketId: number) => {
    if (!contract) return;

    try {
      setListingLoading(ticketId);
      const tx = await contract.cancelListing(ticketId);
      await tx.wait();

      toast.success("🗑 已取消上架");
      // 更新 UI 狀態
      setTickets((prev) =>
        prev.map((t) =>
          t.ticketId === ticketId ? { ...t, isListed: false } : t
        )
      );
    } catch (err: any) {
      if (err.message?.includes("user rejected")) {
        toast.error("你取消了交易簽章");
      } else {
        toast.error("取消上架失敗");
      }
    } finally {
      setListingLoading(null);
    }
  };

  const handleGenerateSignature = async (ticketId: number) => {
    if (!signer) return;

    const timestamp = Math.floor(Date.now() / 1000);
    const message = `Check-in ticketId: ${ticketId} at ${timestamp}`;

    try {
      const signature = await signer.signMessage(message);
      setSignatures((prev) => ({
        ...prev,
        [ticketId]: { message, signature, timestamp },
      }));
    } catch (err) {
      console.error("簽章失敗", err);
    }
  };

  useEffect(() => {
    const fetchTickets = async () => {
      if (!contract || !account) return;
      setLoading(true);

      try {
        const balance = await contract.balanceOf(account);
        const ticketIds = await Promise.all(
          Array.from({ length: Number(balance) }).map((_, i) =>
            contract.tokenOfOwnerByIndex(account, i)
          )
        );

        const ticketData = await Promise.all(
          ticketIds.map(async (ticketId) => {
            const [eventId, checkedInAt, tokenUri, listing, isSBT] =
              await Promise.all([
                contract.ticketToEvent(ticketId),
                contract.getCheckInTimestamp(ticketId),
                contract.tokenURI(ticketId),
                contract.listings(ticketId),
                contract.isTicketSoulBound(ticketId),
              ]);

            const eventData = await contract.events(eventId);

            const imageUrl = tokenUri.startsWith("ipfs://")
              ? tokenUri.replace("ipfs://", "https://ipfs.io/ipfs/")
              : tokenUri;

            return {
              ticketId: Number(ticketId),
              eventId: Number(eventId),
              eventName: eventData.name,
              checkedInAt: Number(checkedInAt),
              imageUrl,
              isListed: listing.active,
              isSoulBound: isSBT,
            };
          })
        );

        setTickets(ticketData);
      } catch (err) {
        console.error("票券查詢失敗", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, [contract, account]);

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        我的票券
      </Typography>

      {loading ? (
        <CircularProgress />
      ) : tickets.length === 0 ? (
        <Typography>你尚未擁有任何票券</Typography>
      ) : (
        <Grid container spacing={2}>
          {tickets.map((ticket) => (
            <Grid size={{ xs: 12, md: 6, lg: 3 }} key={ticket.ticketId}>
              <Card
                variant="outlined"
                sx={{
                  minHeight: 450,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <CardContent sx={{ flexGrow: 1, overflowY: "auto" }}>
                  <Typography variant="h6">{ticket.eventName}</Typography>
                  <Typography>票券 ID: {ticket.ticketId}</Typography>
                  <Typography>活動 ID: {ticket.eventId}</Typography>
                  <Typography
                    color={ticket.checkedInAt ? "success.main" : "error"}
                  >
                    {ticket.checkedInAt
                      ? `已驗票：${new Date(
                          ticket.checkedInAt * 1000
                        ).toLocaleString()}`
                      : "尚未驗票"}
                  </Typography>
                  <Box mt={2} display="flex" justifyContent="center">
                    <img
                      src={ticket.imageUrl}
                      alt={`ticket-${ticket.ticketId}`}
                      style={{ width: "100%", maxWidth: 300, borderRadius: 8 }}
                    />
                  </Box>

                  {!ticket.checkedInAt && !ticket.isListed && (
                    <>
                      <Box mt={2}>
                        <Button
                          variant="contained"
                          fullWidth
                          onClick={() =>
                            handleGenerateSignature(ticket.ticketId)
                          }
                        >
                          產生簽章
                        </Button>
                      </Box>

                      {signatures[ticket.ticketId] && (
                        <Box mt={2}>
                          <Typography fontWeight="bold">
                            驗票 QR Code:
                          </Typography>
                          <Box mt={1} display="flex" justifyContent="center">
                            <QRCodeCanvas
                              value={JSON.stringify({
                                ticketId: ticket.ticketId,
                                timestamp:
                                  signatures[ticket.ticketId].timestamp,
                                message: signatures[ticket.ticketId].message,
                                signature:
                                  signatures[ticket.ticketId].signature,
                              })}
                              size={200}
                            />
                          </Box>
                        </Box>
                      )}

                      {!ticket.isSoulBound && (
                        <Box mt={3}>
                          <Typography fontWeight="bold">
                            上架票券（ETH）
                          </Typography>
                          <input
                            type="number"
                            placeholder="輸入價格"
                            value={listingPrices[ticket.ticketId] || ""}
                            onChange={(e) =>
                              setListingPrices((prev) => ({
                                ...prev,
                                [ticket.ticketId]: e.target.value,
                              }))
                            }
                            style={{
                              width: "100%",
                              padding: "8px",
                              marginTop: "8px",
                              border: "1px solid #ccc",
                              borderRadius: "4px",
                            }}
                          />
                          <Button
                            variant="contained"
                            color="success"
                            fullWidth
                            sx={{ mt: 1 }}
                            disabled={listingLoading === ticket.ticketId}
                            onClick={() => handleListTicket(ticket.ticketId)}
                          >
                            {listingLoading === ticket.ticketId
                              ? "上架中..."
                              : "📤 上架出售"}
                          </Button>
                        </Box>
                      )}
                    </>
                  )}
                  {ticket.isListed && (
                    <Box mt={2}>
                      <Typography color="warning.main" fontWeight="bold">
                        此票券正在架上販售中
                      </Typography>
                      <Button
                        variant="outlined"
                        color="secondary"
                        fullWidth
                        sx={{ mt: 1 }}
                        disabled={listingLoading === ticket.ticketId}
                        onClick={() => handleCancelListing(ticket.ticketId)}
                      >
                        {listingLoading === ticket.ticketId
                          ? "取消中..."
                          : "🗑 取消上架"}
                      </Button>
                    </Box>
                  )}
                  {ticket.isSoulBound && (
                    <Typography color="info.main" fontWeight="bold" mt={2}>
                      此票券為 Soul Bound Token，無法轉讓或上架
                    </Typography>
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
