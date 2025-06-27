import { useEffect } from "react";
import { RouterProvider } from "react-router";
import { router } from "./router/routes";
import { useLiff } from "./hooks/useLiff";

// Import modules
import { bookingModule } from "./modules/booking/booking-module";
import { ecommerceModule } from "./modules/ecommerce/ecommerce-module";

// Import registry
import { moduleRegistry } from "./lib/module-registry";

function App() {
  const liffState = useLiff();

  // Register modules on component mount
  useEffect(() => {
    moduleRegistry.register(bookingModule);
    moduleRegistry.register(ecommerceModule);
  }, []);

  // Loading state
  if (liffState.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在初始化 LIFF...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (liffState.error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center p-6 max-w-md">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            初始化失敗
          </h2>
          <p className="text-gray-600 mb-4">{liffState.error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            重新載入
          </button>
        </div>
      </div>
    );
  }

  // Success state - show main app
  if (liffState.isLoggedIn && liffState.isInitialized) {
    return <RouterProvider router={router} />;
  }

  // Fallback
  return null;
}

export default App;
