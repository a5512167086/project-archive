import { lazy } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { BaseWrapper } from '@/components/BaseWrapper'
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
const ModulePage = lazy(() =>
  import('@/pages/ModulePage').then((module) => ({
    default: module.ModulePage
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

export const PAGE_PATHS = {
  BASE: '/',
  SIGN_IN: '/sign-in',
  SIGN_UP: '/sign-up',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  OAUTH_CALLBACK: '/oauth-callback',
  BOT_LIST: '/bot-list',
  CREATE_BOT_TURTROIAL: '/bot-tutorial',
  MODULE_LIST: '/module-list',
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
        path: PAGE_PATHS.CREATE_BOT_TURTROIAL,
        element: <CreateBotTutorialPage />
      },
      {
        element: <PrivateRoute />,
        children: [
          {
            path: PAGE_PATHS.BOT_LIST,
            element: <BotPage />
          },
          {
            path: PAGE_PATHS.MODULE_LIST,
            element: <ModulePage />
          }
        ]
      },
      {
        path: PAGE_PATHS.NOT_FOUND,
        element: <NotFoundPage />
      }
    ]
  }
])
