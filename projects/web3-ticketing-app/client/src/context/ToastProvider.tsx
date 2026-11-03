// src/context/ToastContext.tsx
import { createContext, useContext, useState } from "react";
import { Snackbar, Alert, AlertColor } from "@mui/material";

interface ToastContextType {
  success: (msg: string) => void;
  error: (msg: string) => void;
}

const ToastContext = createContext<ToastContextType>({
  success: () => {},
  error: () => {},
});

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState<AlertColor>("success");

  const show = (msg: string, type: AlertColor) => {
    setMessage(msg);
    setSeverity(type);
    setOpen(true);
  };

  const handleClose = () => setOpen(false);

  const toast = {
    success: (msg: string) => show(msg, "success"),
    error: (msg: string) => show(msg, "error"),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <Snackbar
        open={open}
        autoHideDuration={5000}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={severity} variant="filled" onClose={handleClose}>
          {message}
        </Alert>
      </Snackbar>
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);
