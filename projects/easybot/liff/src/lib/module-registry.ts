import type { AppModule } from "../types/module";

class ModuleRegistry {
  private modules: Map<string, AppModule> = new Map();

  register(module: AppModule) {
    this.modules.set(module.config.id, module);
  }

  unregister(moduleId: string) {
    this.modules.delete(moduleId);
  }

  getModule(moduleId: string): AppModule | undefined {
    return this.modules.get(moduleId);
  }

  getAllModules(): AppModule[] {
    return Array.from(this.modules.values());
  }

  getModuleConfigs(): AppModule["config"][] {
    return this.getAllModules().map((module) => module.config);
  }
}

export const moduleRegistry = new ModuleRegistry();
