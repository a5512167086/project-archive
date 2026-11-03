import { WalletProvider } from "@/context/WalletContext";
import { RouterProvider } from "react-router";
import { router } from "@/router";
import { ToastProvider } from "@/context/ToastProvider";

function App() {
  return (
    <WalletProvider>
      <ToastProvider>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            minHeight: "100vh",
          }}
        >
          <RouterProvider router={router} />
        </div>
      </ToastProvider>
    </WalletProvider>
  );
}

export default App;
