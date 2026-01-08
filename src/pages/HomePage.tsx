import { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router"; // 或 react-router-dom
import { DynamicTabs } from "../components/DynamicTabs";
import { useLiff } from "../hooks/useLiff";
import { useGetModuleSettingsQuery, ModuleType } from "../store/apis/moduleApi";
import type { AppModule } from "../types/module";
import { reservationModule } from "../modules/reservation/ReservationModule";
import { ecommerceModule } from "../modules/ecommerce/EcommerceModule";

import { moduleRegistry } from "../lib/module-registry";

const MODULE_MAPPING: Partial<Record<ModuleType, AppModule>> = {
  [ModuleType.Reservation]: reservationModule,
  [ModuleType.Ecomm]: ecommerceModule,
};

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { botUUID } = useLiff();

  const { data: moduleSettings, isLoading } = useGetModuleSettingsQuery(
    botUUID || "",
    { skip: !botUUID }
  );

  const [availableModules, setAvailableModules] = useState<AppModule[]>([]);

  useEffect(() => {
    if (!moduleSettings) return;

    const enabledModules: AppModule[] = [];
    moduleSettings.forEach((setting) => {
      const frontendModule = MODULE_MAPPING[setting.chinese_name];

      if (setting.is_enabled && frontendModule) {
        moduleRegistry.register(frontendModule);
        enabledModules.push(frontendModule);
      }
    });

    setAvailableModules(enabledModules);
  }, [moduleSettings]);

  const activeModuleId = searchParams.get("module");

  const currentActiveModule = useMemo(() => {
    if (availableModules.length === 0) return "";

    // 🔥 修正點：改用 m.config.id
    const found = availableModules.find((m) => m.config.id === activeModuleId);

    // 🔥 修正點：改用 found.config.id
    if (found) return found.config.id;

    // 🔥 修正點：改用 availableModules[0].config.id
    return availableModules[0].config.id;
  }, [availableModules, activeModuleId]);

  useEffect(() => {
    if (currentActiveModule && currentActiveModule !== activeModuleId) {
      setSearchParams({ module: currentActiveModule }, { replace: true });
    }
  }, [currentActiveModule, activeModuleId, setSearchParams]);

  const handleModuleChange = (moduleId: string) => {
    setSearchParams({ module: moduleId });
  };

  if (isLoading) {
    return <div className="p-4 text-center">載入模組設定中...</div>;
  }

  if (!isLoading && availableModules.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        目前沒有可用的功能模組。
      </div>
    );
  }

  return (
    <div className="space-y-4 flex flex-1">
      <DynamicTabs
        modules={availableModules}
        activeModule={currentActiveModule}
        onModuleChange={handleModuleChange}
      />
    </div>
  );
}
