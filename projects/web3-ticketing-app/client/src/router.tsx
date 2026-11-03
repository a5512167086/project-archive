import { createBrowserRouter } from "react-router";
import BaseLayout from "@/components/BaseLayout";
import Homepage from "@/pages/Homepage";
import MyTicketPage from "@/pages/MyTicketPage";
import CheckInPage from "@/pages/CheckInPage";
import MyEventsPage from "@/pages/MyEventsPage";
import SecondaryMarketPage from "@/pages/SecondaryMarketPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <BaseLayout />, // 套用 layout
    children: [
      { index: true, element: <Homepage /> },
      { path: "my-tickets", element: <MyTicketPage /> },
      { path: "check-in", element: <CheckInPage /> },
      { path: "my-events", element: <MyEventsPage /> },
      { path: "secondary-market", element: <SecondaryMarketPage /> },
    ],
  },
]);
