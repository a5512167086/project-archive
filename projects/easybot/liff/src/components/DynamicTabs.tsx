import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { AppModule } from "../types/module";

interface DynamicTabsProps {
  modules: AppModule[];
  activeModule: string;
  onModuleChange: (moduleId: string) => void;
}

export function DynamicTabs({
  modules,
  activeModule,
  onModuleChange,
}: DynamicTabsProps) {
  return (
    <Tabs
      value={activeModule}
      onValueChange={onModuleChange}
      className="w-full flex flex-col flex-1"
    >
      {/* 修改處 1: 改用 flex 並確保寬度為 full */}
      <TabsList className="flex w-full h-auto p-1">
        {modules.map((module) => {
          const Icon = module.config.icon;
          return (
            <TabsTrigger
              key={module.config.id}
              value={module.config.id}
              // 修改處 2: 加上 flex-1 讓每個 Tab 平均分配寬度
              className="flex-1 flex items-center justify-center space-x-2 py-2"
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{module.config.name}</span>
            </TabsTrigger>
          );
        })}
      </TabsList>

      {modules.map((module) => (
        <TabsContent
          key={module.config.id}
          value={module.config.id}
          className="mt-4 flex-1"
        >
          {module.component.render()}
        </TabsContent>
      ))}
    </Tabs>
  );
}
