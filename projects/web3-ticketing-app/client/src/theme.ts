import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#1976d2", // Modern blue
    },
    secondary: {
      main: "#ff9800", // Accent orange
    },
    background: {
      default: "#f5f5f5", // Light gray for page background
      paper: "#ffffff", // White for main card content
    },
    text: {
      primary: "#212121", // Almost black
      secondary: "#616161", // Gray
    },
    error: {
      main: "#e53935",
    },
  },
  typography: {
    fontFamily: "'Inter', 'Helvetica', 'Arial', sans-serif",
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          borderRadius: 8,
          "&.Mui-disabled": {
            backgroundColor: "#90caf9",
            color: "#ffffff",
            opacity: 1,
          },
        } as any, // 👉 告訴 TS 不要檢查這段 object literal
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "#ffffff",
          color: "#212121",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
        },
      },
    },
  },
});

export default theme;
