import { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import { DynamicTabs } from "../components/DynamicTabs";

// Import modules
import { bookingModule } from "../modules/booking/booking-module";
import { ecommerceModule } from "../modules/ecommerce/ecommerce-module";

// Import registry
import { moduleRegistry } from "../lib/module-registry";
import type { AppModule } from "../types/module";

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [availableModules, setAvailableModules] = useState<AppModule[]>([]);

  // 從 URL 參數獲取當前模組，默認為 booking
  const activeModule = searchParams.get("module") || "booking";

  // Register modules on component mount
  useEffect(() => {
    // Register default modules
    moduleRegistry.register(bookingModule);
    moduleRegistry.register(ecommerceModule);

    // Get all registered modules
    setAvailableModules(moduleRegistry.getAllModules());
  }, []);

  const handleModuleChange = (moduleId: string) => {
    setSearchParams({ module: moduleId });
  };

  return (
    <div className="space-y-4">
      <DynamicTabs
        modules={availableModules}
        activeModule={activeModule}
        onModuleChange={handleModuleChange}
      />
    </div>
  );
}
