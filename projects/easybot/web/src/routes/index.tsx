import { lazy } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { BaseWrapper } from '@/components/BaseWrapper'
import { SidebarWrapper } from '@/components/SidebarWrapper/SidebarWrapper'
import QuizIcon from '@mui/icons-material/Quiz'
import SettingsApplicationsIcon from '@mui/icons-material/SettingsApplications'
import StoreIcon from '@mui/icons-material/Store'
import EventNoteIcon from '@mui/icons-material/EventNote'
import BackspaceIcon from '@mui/icons-material/Backspace'
import SettingsIcon from '@mui/icons-material/Settings'
import ViewListIcon from '@mui/icons-material/ViewList'
import RoomServiceIcon from '@mui/icons-material/RoomService'
import InventoryIcon from '@mui/icons-material/Inventory'
import PrivateRoute from '@/components/PrivateRoute/PrivateRoute'

const SignInPage = lazy(() => import('@/pages/SignInPage'))
const SignUpPage = lazy(() => import('@/pages/SignUpPage'))
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'))
const OAuthCallback = lazy(() => import('@/pages/OAuthCallbackPage'))
const BotManagementPage = lazy(() => import('@/pages/BotManagementPage'))
const OrderManagementPage = lazy(() => import('@/pages/OrderManagementPage'))
const EcommSettingPage = lazy(() => import('@/pages/EcommSettingPage'))
const KnowledgeManagementPage = lazy(
  () => import('@/pages/KnowledgeManagementPage')
)
const ReservationManagementPage = lazy(
  () => import('@/pages/ReservationManagementPage')
)
const ProductManagementPage = lazy(
  () => import('@/pages/ProductManagementPage')
)
const UpdateProductPage = lazy(() => import('@/pages/UpdateProductPage'))
const ServiceManagementPage = lazy(
  () => import('@/pages/ServiceManagementPage')
)
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))
const Homepage = lazy(() => import('@/pages/Homepage'))
const BotPage = lazy(() => import('@/pages/BotPage'))
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage'))
const CreateBotTutorialPage = lazy(
  () => import('@/pages/CreateBotTutorialPage')
)
const BotSettingPage = lazy(() => import('@/pages/BotSettingPage'))
const UserSettingPage = lazy(() => import('@/pages/UserSettingPage'))

export const PAGE_PATHS = {
  BASE: '/',
  USER_SETTING: '/user-setting',
  SIGN_IN: '/sign-in',
  SIGN_UP: '/sign-up',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  OAUTH_CALLBACK: '/oauth-callback',
  BOT_LIST: '/bot-list',
  BOT_MANAGEMENT: '/bot-list/:uuid',
  PRODUCT_MANAGEMENT: 'product',
  UPDATE_PRODUCT: 'product/:productId',
  ORDER_MANAGEMENT: 'order',
  ECOMM_SETTING: 'ecomm',
  BOT_SETTING: 'setting',
  RESERVATION_MANAGEMENT: 'reservation',
  SERVICE_MANAGEMENT: 'service',
  KNOWLEDGE_MOUDLE: 'knowledge',
  CREATE_BOT_TURTROIAL: '/bot-tutorial',
  NOT_FOUND: '*'
}

export const PUBLIC_NAVIGATION_ROUTE = [
  { text: 'header.home', link: PAGE_PATHS.BASE },
  { text: 'header.signIn', link: PAGE_PATHS.SIGN_IN },
  { text: 'header.signUp', link: PAGE_PATHS.SIGN_UP }
]

export const PRIVATE_NAVIGATION_ROUTE = [
  { text: 'botPage.myBot', link: PAGE_PATHS.BOT_LIST },
  { text: 'header.userSetting', link: PAGE_PATHS.USER_SETTING }
]

export const REDIRECT_BOT_LIST_ROUTES = [
  PAGE_PATHS.BASE,
  PAGE_PATHS.SIGN_IN,
  PAGE_PATHS.SIGN_UP,
  PAGE_PATHS.OAUTH_CALLBACK,
  PAGE_PATHS.RESET_PASSWORD,
  PAGE_PATHS.FORGOT_PASSWORD
]

export const SIDEBAR_NAVIGATION_ROUTE = [
  {
    key: 'modules',
    items: [
      {
        key: 'moduleList',
        text: 'sidebar.moduleList',
        icon: <ViewListIcon />,
        link: PAGE_PATHS.BOT_LIST
      },
      {
        key: 'faq',
        text: 'sidebar.faq',
        icon: <QuizIcon />,
        link: PAGE_PATHS.KNOWLEDGE_MOUDLE
      }
    ]
  },
  {
    key: 'ecomm',
    items: [
      {
        key: 'product',
        text: 'sidebar.product',
        icon: <InventoryIcon />,
        link: PAGE_PATHS.PRODUCT_MANAGEMENT
      },
      {
        key: 'order',
        text: 'sidebar.order',
        icon: <StoreIcon />,
        link: PAGE_PATHS.ORDER_MANAGEMENT
      },
      {
        key: 'ecommSetting',
        text: 'sidebar.ecomm',
        icon: <SettingsApplicationsIcon />,
        link: PAGE_PATHS.ECOMM_SETTING
      }
    ]
  },
  {
    key: 'reservation',
    items: [
      {
        key: 'service',
        text: 'sidebar.service',
        icon: <RoomServiceIcon />,
        link: PAGE_PATHS.SERVICE_MANAGEMENT
      },
      {
        key: 'reservation',
        text: 'sidebar.reservation',
        icon: <EventNoteIcon />,
        link: PAGE_PATHS.RESERVATION_MANAGEMENT
      }
    ]
  },
  {
    key: 'settings',
    items: [
      {
        key: 'setting',
        text: 'sidebar.bot',
        icon: <SettingsIcon />,
        link: PAGE_PATHS.BOT_SETTING
      }
    ]
  },
  {
    key: 'system',
    items: [
      {
        key: 'backToBotList',
        text: 'sidebar.backToBotList',
        icon: <BackspaceIcon />,
        link: PAGE_PATHS.BOT_LIST
      }
    ]
  }
]

export const router = createBrowserRouter([
  // Public routes
  {
    path: PAGE_PATHS.BASE,
    element: <BaseWrapper />,
    children: [
      {
        index: true,
        element: <Homepage />
      },
      {
        path: PAGE_PATHS.SIGN_IN,
        element: <SignInPage />
      },
      {
        path: PAGE_PATHS.SIGN_UP,
        element: <SignUpPage />
      },
      {
        path: PAGE_PATHS.FORGOT_PASSWORD,
        element: <ForgotPasswordPage />
      },
      {
        path: PAGE_PATHS.RESET_PASSWORD,
        element: <ResetPasswordPage />
      },
      // Private routes
      {
        path: PAGE_PATHS.USER_SETTING,
        element: <PrivateRoute />,
        children: [
          {
            index: true,
            element: <UserSettingPage />
          }
        ]
      },
      {
        path: PAGE_PATHS.BOT_LIST,
        element: <PrivateRoute />,
        children: [
          {
            index: true,
            element: <BotPage />
          }
        ]
      },
      // Public routes
      {
        path: PAGE_PATHS.CREATE_BOT_TURTROIAL,
        element: <CreateBotTutorialPage />
      }
    ]
  },
  {
    path: PAGE_PATHS.OAUTH_CALLBACK,
    element: <OAuthCallback />
  },
  {
    path: PAGE_PATHS.NOT_FOUND,
    element: <NotFoundPage />
  },
  // Private routes
  {
    path: PAGE_PATHS.BOT_MANAGEMENT,
    element: <PrivateRoute />,
    children: [
      {
        element: <SidebarWrapper />,
        children: [
          {
            index: true,
            element: <BotManagementPage />
          },
          {
            path: PAGE_PATHS.KNOWLEDGE_MOUDLE,
            element: <KnowledgeManagementPage />
          },
          {
            path: PAGE_PATHS.ORDER_MANAGEMENT,
            element: <OrderManagementPage />
          },
          {
            path: PAGE_PATHS.ECOMM_SETTING,
            element: <EcommSettingPage />
          },
          {
            path: PAGE_PATHS.PRODUCT_MANAGEMENT,
            element: <ProductManagementPage />
          },
          {
            path: PAGE_PATHS.UPDATE_PRODUCT,
            element: <UpdateProductPage />
          },
          {
            path: PAGE_PATHS.RESERVATION_MANAGEMENT,
            element: <ReservationManagementPage />
          },
          {
            path: PAGE_PATHS.SERVICE_MANAGEMENT,
            element: <ServiceManagementPage />
          },
          {
            path: PAGE_PATHS.BOT_SETTING,
            element: <BotSettingPage />
          }
        ]
      }
    ]
  }
])
