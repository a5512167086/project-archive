import { useEffect } from "react";
import { RouterProvider } from "react-router";
import { router } from "./router/routes";
import { useLiff } from "./hooks/useLiff";
import { LiffLoading } from "./components/common/LiffLoading";
import { LiffError } from "./components/common/LiffError";

// Import modules
import { reservationModule } from "./modules/reservation/ReservationModule";
import { ecommerceModule } from "./modules/ecommerce/EcommerceModule";

// Import registry
import { moduleRegistry } from "./lib/module-registry";

function App() {
  const liffState = useLiff();

  // Register modules on component mount
  useEffect(() => {
    moduleRegistry.register(reservationModule);
    moduleRegistry.register(ecommerceModule);
  }, []);

  // Loading state
  if (liffState.isLoading) {
    return <LiffLoading />;
  }

  // Error state
  if (liffState.error) {
    return <LiffError error={liffState.error} />;
  }

  // Success state - show main app
  if (liffState.isLoggedIn && liffState.isInitialized) {
    return <RouterProvider router={router} />;
  }

  // Fallback
  return null;
}

export default App;

