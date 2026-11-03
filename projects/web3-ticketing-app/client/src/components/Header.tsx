import {
  AppBar,
  Button,
  Toolbar,
  Typography,
  Box,
  Chip,
  Tooltip,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import { useWallet } from "@/context/WalletContext";
import { useNavigate } from "react-router";
import { useState } from "react";
import CloseIcon from "@mui/icons-material/Close";

export default function Header() {
  const { account, connectWallet } = useWallet();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [drawerOpen, setDrawerOpen] = useState(false);

  const formatAddress = (addr: string) =>
    `${addr.slice(0, 6)}...${addr.slice(-4)}`;

  const menuItems = [
    { text: "二級市場", path: "/secondary-market" },
    { text: "我的活動", path: "/my-events" },
    { text: "我的票券", path: "/my-tickets" },
  ];

  const renderMenuButtons = () =>
    menuItems.map((item) => (
      <Button
        key={item.path}
        variant="outlined"
        onClick={() => navigate(item.path)}
        sx={{ textTransform: "none" }}
      >
        {item.text}
      </Button>
    ));

  return (
    <>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
          <Typography
            variant="h6"
            onClick={() => navigate("/")}
            sx={{ cursor: "pointer", userSelect: "none" }}
          >
            Web3 Ticketing
          </Typography>

          <Box display="flex" alignItems="center" gap={2}>
            {/* 桌面版按鈕 */}
            {!isMobile && account && renderMenuButtons()}

            {/* 桌面 & 手機錢包狀態 */}
            {!account ? (
              <Button
                variant="contained"
                color="warning"
                onClick={connectWallet}
                sx={{ textTransform: "none" }}
              >
                連接 MetaMask
              </Button>
            ) : (
              <Tooltip title={account}>
                <Chip
                  label={formatAddress(account)}
                  color="success"
                  variant="outlined"
                  size="small"
                />
              </Tooltip>
            )}

            {/* 手機版漢堡選單 */}
            {isMobile && account && (
              <IconButton onClick={() => setDrawerOpen(true)}>
                <MenuIcon sx={{ color: "black" }} />
              </IconButton>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box
          sx={{
            width: "100vw",
            height: "100vh",
            display: "flex",
            flexDirection: "column",
          }}
          role="presentation"
        >
          {/* 關閉按鈕 */}
          <Box sx={{ display: "flex", justifyContent: "flex-end", p: 2 }}>
            <IconButton onClick={() => setDrawerOpen(false)}>
              <CloseIcon sx={{ color: "black" }} />
            </IconButton>
          </Box>

          {/* 選單項目 */}
          <Box
            sx={{
              flex: 1,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <List sx={{ width: "100%", maxWidth: 300 }}>
              {menuItems.map((item) => (
                <ListItem
                  key={item.path}
                  disablePadding
                  sx={{
                    justifyContent: "center",
                    mb: 2,
                    border: "1px solid #e0e0e0",
                    borderRadius: "8px",
                    mx: "auto",
                    width: "80%",
                  }}
                >
                  <ListItemButton
                    onClick={() => {
                      navigate(item.path);
                      setDrawerOpen(false);
                    }}
                    sx={{
                      justifyContent: "center",
                      textAlign: "center",
                      transition: "background-color 0.2s ease",
                      "&:hover": {
                        backgroundColor: "#f5f5f5",
                      },
                    }}
                  >
                    <ListItemText
                      primary={item.text}
                      primaryTypographyProps={{
                        fontSize: "1.1rem",
                        fontWeight: 500,
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        </Box>
      </Drawer>
    </>
  );
}
