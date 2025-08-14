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
      <TabsList className={`grid w-full grid-cols-${modules.length}`}>
        {modules.map((module) => {
          const Icon = module.config.icon;
          return (
            <TabsTrigger
              key={module.config.id}
              value={module.config.id}
              className="flex items-center space-x-2"
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
