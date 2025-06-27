import { useNavigate } from "react-router";
import { ShoppingBag, Package, Heart, Calendar } from "lucide-react";
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
  const liffState = useLiff();
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
      id: "appointments",
      icon: Calendar,
      title: "我的預約",
      description: "管理預約記錄",
      color: "green" as const,
      path: "/appointments",
    },
    {
      id: "favorites",
      icon: Heart,
      title: "我的收藏",
      description: "收藏的商品",
      color: "red" as const,
      path: "/home?module=ecommerce",
    },
    {
      id: "cart",
      icon: ShoppingBag,
      title: "購物車",
      description: "待結帳商品",
      color: "purple" as const,
      path: "/home?module=ecommerce",
    },
  ];

  const handleQuickActionClick = (path: string) => {
    navigate(path);
  };

  // 使用 LIFF 的用戶資訊
  const userName = liffState.userProfile?.displayName || "用戶";
  const userAvatar =
    liffState.userProfile?.pictureUrl || "https://via.placeholder.com/64";

  return (
    <div className="space-y-4">
      <UserProfileCard
        name={userName}
        memberLevel="金卡會員"
        points={2580}
        avatar={userAvatar}
      />

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

      {/* Debug info (只在開發環境顯示) */}
      {import.meta.env.DEV && liffState.userProfile && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Debug Info</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
              {JSON.stringify(liffState.userProfile, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
