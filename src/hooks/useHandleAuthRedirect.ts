import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { PAGE_PATHS, REDIRECT_BOT_LIST_ROUTES } from '@/routes'

export const useHandleAuthRedirect = (
  isAuthenticated: boolean,
  isAuthFailed: boolean,
  onAuthFailed: () => void,
  onRedirect?: () => void
) => {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const isInRedirectRoutes = REDIRECT_BOT_LIST_ROUTES.includes(
      location.pathname
    )

    if (isAuthenticated && isInRedirectRoutes) {
      navigate(PAGE_PATHS.BOT_LIST)
      onRedirect?.()
    } else if (isAuthFailed) {
      onAuthFailed()
    }
  }, [
    isAuthenticated,
    isAuthFailed,
    location.pathname,
    navigate,
    onAuthFailed,
    onRedirect
  ])
}
