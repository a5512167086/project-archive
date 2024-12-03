import { lazy } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { BaseWrapper } from '@/components/BaseWrapper'
import { SidebarWrapper } from '@/components/SidebarWrapper/SidebarWrapper'
import QuizIcon from '@mui/icons-material/Quiz'
import StoreIcon from '@mui/icons-material/Store'
import EventNoteIcon from '@mui/icons-material/EventNote'
import BackspaceIcon from '@mui/icons-material/Backspace'
import SettingsIcon from '@mui/icons-material/Settings'
import ViewListIcon from '@mui/icons-material/ViewList'
import PrivateRoute from '@/components/PrivateRoute/PrivateRoute'

const SignInPage = lazy(() =>
  import('@/pages/SignInPage').then((module) => ({
    default: module.SignInPage
  }))
)
const SignUpPage = lazy(() =>
  import('@/pages/SignUpPage').then((module) => ({
    default: module.SignUpPage
  }))
)
const ForgotPasswordPage = lazy(() =>
  import('@/pages/ForgotPasswordPage').then((module) => ({
    default: module.ForgotPasswordPage
  }))
)
const OAuthCallback = lazy(() =>
  import('@/pages/OAuthCallbackPage/OAuthCallbackPage').then((module) => ({
    default: module.OAuthCallbackPage
  }))
)
const BotManagementPage = lazy(() =>
  import('@/pages/BotManagementPage').then((module) => ({
    default: module.BotManagementPage
  }))
)
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((module) => ({
    default: module.NotFoundPage
  }))
)
const Homepage = lazy(() =>
  import('@/pages/Homepage').then((module) => ({ default: module.Homepage }))
)
const BotPage = lazy(() =>
  import('@/pages/BotPage').then((module) => ({ default: module.BotPage }))
)
const ResetPasswordPage = lazy(() =>
  import('@/pages/ResetPasswordPage').then((module) => ({
    default: module.ResetPasswordPage
  }))
)
const CreateBotTutorialPage = lazy(() =>
  import('@/pages/CreateBotTutorialPage').then((module) => ({
    default: module.CreateBotTutorialPage
  }))
)
const BotSettingPage = lazy(() =>
  import('@/pages/BotSettingPage').then((module) => ({
    default: module.BotSettingPage
  }))
)

export const PAGE_PATHS = {
  BASE: '/',
  SIGN_IN: '/sign-in',
  SIGN_UP: '/sign-up',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  OAUTH_CALLBACK: '/oauth-callback',
  BOT_LIST: '/bot-list',
  BOT_MANAGEMENT: '/bot-list/:uuid',
  FAQ_MODULE: 'faq',
  ECOMM_MODULE: 'ecomm',
  BOT_SETTING: 'setting',
  RESERVATION_MODULE: 'reservation',
  CREATE_BOT_TURTROIAL: '/bot-tutorial',
  NOT_FOUND: '*'
}

export const PUBLIC_NAVIGATION_ROUTE = [
  { text: 'header.home', link: PAGE_PATHS.BASE },
  { text: 'header.signIn', link: PAGE_PATHS.SIGN_IN },
  { text: 'header.signUp', link: PAGE_PATHS.SIGN_UP }
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
    key: 'moduleList',
    text: 'sidebar.moduleList',
    icon: <ViewListIcon />,
    link: PAGE_PATHS.BOT_LIST
  },
  {
    key: 'faq',
    text: 'sidebar.faq',
    icon: <QuizIcon />,
    link: PAGE_PATHS.FAQ_MODULE
  },
  {
    key: 'ecomm',
    text: 'sidebar.ecomm',
    icon: <StoreIcon />,
    link: PAGE_PATHS.ECOMM_MODULE
  },
  {
    key: 'reservation',
    text: 'sidebar.reservation',
    icon: <EventNoteIcon />,
    link: PAGE_PATHS.RESERVATION_MODULE
  },
  {
    key: 'setting',
    text: 'common.setting',
    icon: <SettingsIcon />,
    link: PAGE_PATHS.BOT_SETTING
  },
  {
    key: 'backToBotList',
    text: 'sidebar.backToBotList',
    icon: <BackspaceIcon />,
    link: PAGE_PATHS.BOT_LIST
  }
]

export const router = createBrowserRouter([
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
      {
        path: PAGE_PATHS.OAUTH_CALLBACK,
        element: <OAuthCallback />
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
      {
        path: PAGE_PATHS.CREATE_BOT_TURTROIAL,
        element: <CreateBotTutorialPage />
      },
      {
        path: PAGE_PATHS.NOT_FOUND,
        element: <NotFoundPage />
      }
    ]
  },
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
            path: PAGE_PATHS.FAQ_MODULE,
            element: <div>test</div>
          },
          {
            path: PAGE_PATHS.ECOMM_MODULE,
            element: <div>test</div>
          },
          {
            path: PAGE_PATHS.RESERVATION_MODULE,
            element: <div>test</div>
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
