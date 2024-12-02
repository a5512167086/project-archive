import { Alert, Box, Snackbar } from '@mui/material'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'
import { StyledBaseWrapper } from './BaseWrapper.style'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Suspense, useEffect, useState } from 'react'
import { CustomLoader } from '../CustomLoader'
import { useTranslation } from 'react-i18next'
import { useClearError } from '@/hooks/useClearError'
import { PAGE_PATHS, REDIRECT_BOT_LIST_ROUTES } from '@/routes'
import { useUser } from '@/hooks/useUser'

const loaderText = 'common.loading'

export const BaseWrapper = () => {
  useClearError()
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const { isAuthenticated, isAuthFailed } = useUser()
  const [isAlertOpen, setAlertOpen] = useState(false)

  const handleClose = () => {
    setAlertOpen(false)
  }

  useEffect(() => {
    const isInRedirectRoutes = REDIRECT_BOT_LIST_ROUTES.includes(
      location.pathname
    )

    if (isAuthenticated && isInRedirectRoutes) {
      navigate(PAGE_PATHS.BOT_LIST)
    } else if (isAuthFailed) {
      setAlertOpen(true)
    }
  }, [isAuthenticated, isAuthFailed, location])

  return (
    <StyledBaseWrapper>
      <Header />
      <Box className="wrapper__content">
        <Suspense fallback={<CustomLoader size="6rem" text={t(loaderText)} />}>
          <Outlet />
          <Snackbar
            open={isAlertOpen}
            autoHideDuration={5000}
            onClose={handleClose}
          >
            <Alert onClose={handleClose} severity="warning">
              {t('error.token_expired')}
            </Alert>
          </Snackbar>
        </Suspense>
      </Box>
      <Footer />
    </StyledBaseWrapper>
  )
}
