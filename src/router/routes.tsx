import { createBrowserRouter, Navigate } from "react-router";
import Layout from "../components/Layout";
import HomePage from "../pages/HomePage";
import ProfilePage from "../pages/ProfilePage";
import OrdersPage from "../pages/OrdersPage";
import ReservationPage from "../pages/ReservationPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Navigate to="/home" replace />,
      },
      {
        path: "home",
        element: <HomePage />,
      },
      {
        path: "profile",
        element: <ProfilePage />,
      },
      {
        path: "orders",
        element: <OrdersPage />,
      },
      {
        path: "reservation",
        element: <ReservationPage />,
      },
    ],
  },
]);
