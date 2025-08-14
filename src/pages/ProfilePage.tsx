import { useNavigate } from "react-router";
import { Package, Calendar } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { QuickActionCard } from "../components/QuickActionCard";
import { UserProfileCard } from "../components/UserProfileCard";
import { moduleRegistry } from "../lib/module-registry";
import { useLiff } from "../hooks/useLiff";

export default function ProfilePage() {
  const navigate = useNavigate();
  const { userProfile, isLoading } = useLiff();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">載入中...</div>
    );
  }
  const availableModules = moduleRegistry.getAllModules();

  const quickActions = [
    {
      id: "orders",
      icon: Package,
      title: "我的訂單",
      description: "查看購買記錄",
      color: "blue" as const,
      path: "/orders",
    },
    {
      id: "reservation",
      icon: Calendar,
      title: "我的預約",
      description: "管理預約記錄",
      color: "green" as const,
      path: "/reservation",
    },
  ];

  const handleQuickActionClick = (path: string) => {
    navigate(path);
  };
  console.log(userProfile);
  const userName = userProfile?.displayName || "用戶";
  const userAvatar = userProfile?.pictureUrl;

  return (
    <div className="space-y-4">
      <UserProfileCard name={userName} avatar={userAvatar} />

      <div className="grid grid-cols-2 gap-4">
        {quickActions.map((action) => (
          <QuickActionCard
            key={action.id}
            icon={action.icon}
            title={action.title}
            description={action.description}
            color={action.color}
            onClick={() => handleQuickActionClick(action.path)}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">可用功能模組</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {availableModules.map((module) => {
              const Icon = module.config.icon;
              return (
                <button
                  key={module.config.id}
                  className="flex items-center space-x-2 p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                  onClick={() => navigate(`/home?module=${module.config.id}`)}
                >
                  <Icon className="h-4 w-4" />
                  <span className="text-sm">{module.config.name}</span>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
