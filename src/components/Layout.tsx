import { Outlet } from "react-router";
import { BottomNavigation } from "./BottomNavigation";

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 pb-20 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="px-4 py-3">
          <h1 className="text-xl font-bold text-center">多功能服務平台</h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col px-4 py-4">
        <Outlet />
      </div>

      {/* Bottom Navigation */}
      <BottomNavigation />
    </div>
  );
}
