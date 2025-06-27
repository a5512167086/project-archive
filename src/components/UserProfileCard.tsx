import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent } from "@/components/ui/card"

interface UserProfileCardProps {
  name: string
  memberLevel: string
  points: number
  avatar?: string
}

export function UserProfileCard({ name, memberLevel, points, avatar }: UserProfileCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center space-x-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={avatar || "/placeholder.svg"} />
            <AvatarFallback>{name}</AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-medium text-lg">{name}</h3>
            <p className="text-sm text-muted-foreground">會員等級：{memberLevel}</p>
            <p className="text-sm text-muted-foreground">積分：{points.toLocaleString()} 點</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
