import { RouterProvider } from "react-router";
import { router } from "./router/routes";
import { useLiff } from "./hooks/useLiff";
import { LiffLoading } from "./components/common/LiffLoading";
import { LiffError } from "./components/common/LiffError";

function App() {
  const liffState = useLiff();

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
