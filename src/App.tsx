import { useEffect } from "react";
import liff from "@line/liff";
import Homepage from "@/pages/Homepage";

function App() {
  useEffect(() => {
    liff
      .init({
        liffId: import.meta.env.VITE_LIFF_ID,
      })
      .then(() => {
        console.log("LIFF init succeeded.");
      })
      .catch((e: Error) => {
        console.log("LIFF init failed", e);
      });
  });

  return <Homepage />;
}

export default App;
