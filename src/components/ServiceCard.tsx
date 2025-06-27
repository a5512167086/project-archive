import type React from "react"
import { Card, CardContent } from "./ui/card"

interface ServiceCardProps {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  color: "blue" | "green" | "purple" | "orange"
  onClick?: () => void
}

const colorClasses = {
  blue: "bg-blue-100 text-blue-600",
  green: "bg-green-100 text-green-600",
  purple: "bg-purple-100 text-purple-600",
  orange: "bg-orange-100 text-orange-600",
}

export function ServiceCard({ icon: Icon, title, description, color, onClick }: ServiceCardProps) {
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <CardContent className="p-4 text-center">
        <div className={`w-12 h-12 ${colorClasses[color]} rounded-full flex items-center justify-center mx-auto mb-2`}>
          <Icon className="h-6 w-6" />
        </div>
        <h3 className="font-medium">{title}</h3>
        <p className="text-sm text-gray-500">{description}</p>
      </CardContent>
    </Card>
  )
}
