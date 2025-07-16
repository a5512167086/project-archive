import { Box } from '@mui/material'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'
import { StyledBaseWrapper } from './BaseWrapper.style'
import { Outlet } from 'react-router-dom'
import { Suspense, useState, useCallback } from 'react'
import { CustomLoader } from '../CustomLoader'
import { useTranslation } from 'react-i18next'
import { useUser } from '@/hooks/useUser'
import { useHandleAuthRedirect } from '@/hooks/useHandleAuthRedirect'
import { CustomAlert } from '../CustomAlert/CustomAlert'
import { useAppSelector } from '@/utils/hook'
import { useErrorHandler } from '@/hooks/useErrorHandler'

const loaderText = 'common.loading'

export const BaseWrapper = () => {
  const { t } = useTranslation()
  const { isAuthFailed, setIsAuthFailed } = useUser()
  const { isAuthenticated } = useAppSelector((state) => state.user)
  const [isAlertOpen, setAlertOpen] = useState(false)

  const handleAuthFailed = useCallback(() => {
    setAlertOpen(true)
    setIsAuthFailed(false)
  }, [setIsAuthFailed])

  useErrorHandler()

  useHandleAuthRedirect(isAuthenticated, isAuthFailed, handleAuthFailed)
  return (
    <StyledBaseWrapper>
      <Header />
      <Box className="wrapper__content">
        <Suspense fallback={<CustomLoader size="6rem" text={t(loaderText)} />}>
          <Outlet />
          <CustomAlert
            open={isAlertOpen}
            message={t('error.token_expired')}
            onClose={() => setAlertOpen(false)}
          />
        </Suspense>
      </Box>
      <Footer />
    </StyledBaseWrapper>
  )
}
