import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";

interface UserProfileCardProps {
  name: string;
  avatar?: string;
}

export function UserProfileCard({ name, avatar }: UserProfileCardProps) {
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
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
