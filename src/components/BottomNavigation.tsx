import { NavLink } from "react-router";
import { ShoppingBag, Package, Clock, User } from "lucide-react";

const navItems = [
  { id: "home", path: "/home", icon: ShoppingBag, label: "首頁" },
  { id: "orders", path: "/orders", icon: Package, label: "訂單" },
  { id: "appointments", path: "/appointments", icon: Clock, label: "預約" },
  { id: "profile", path: "/profile", icon: User, label: "個人" },
];

export function BottomNavigation() {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t">
      <div className="grid grid-cols-4 py-2">
        {navItems.map(({ id, path, icon: Icon, label }) => (
          <NavLink
            key={id}
            to={path}
            className={({ isActive }) =>
              `flex flex-col items-center py-2 px-1 ${
                isActive ? "text-blue-600" : "text-gray-600"
              }`
            }
          >
            <Icon className="h-5 w-5 mb-1" />
            <span className="text-xs">{label}</span>
          </NavLink>
        ))}
      </div>
    </div>
  );
}
