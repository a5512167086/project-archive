import type React from "react"

export interface ModuleConfig {
  id: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  description?: string
}

export interface ModuleComponent {
  id: string
  render: () => React.ReactNode
}

export interface AppModule {
  config: ModuleConfig
  component: ModuleComponent
}
