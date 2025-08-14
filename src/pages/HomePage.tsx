import { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import { DynamicTabs } from "../components/DynamicTabs";

// Import modules
import { reservationModule } from "../modules/reservation/ReservationModule";
import { ecommerceModule } from "../modules/ecommerce/EcommerceModule";

// Import registry
import { moduleRegistry } from "../lib/module-registry";
import type { AppModule } from "../types/module";

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [availableModules, setAvailableModules] = useState<AppModule[]>([]);

  // 從 URL 參數獲取當前模組，默認為 booking
  const activeModule = searchParams.get("module") || "reservation";

  // Register modules on component mount
  useEffect(() => {
    // Register default modules
    moduleRegistry.register(reservationModule);
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
