import { Box, Typography } from "@mui/material";

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: "auto",
        textAlign: "center",
        backgroundColor: (theme) => theme.palette.background.paper,
        color: (theme) => theme.palette.text.secondary,
        borderTop: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <Typography variant="body2">
        © {new Date().getFullYear()} Shin(113321531) — All Rights Reserved.
      </Typography>
    </Box>
  );
}
