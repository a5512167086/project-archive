import { Link } from "react-router";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";

export default function OrdersPage() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg text-center">訂單功能</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <div className="py-8">
            <div className="text-6xl mb-4">📦</div>
            <h3 className="text-lg font-medium mb-2">訂單功能暫未開放</h3>
            <p className="text-muted-foreground mb-4">
              目前主要提供預約服務功能
            </p>
            <Link to="/appointments">
              <Button>前往預約頁面</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
