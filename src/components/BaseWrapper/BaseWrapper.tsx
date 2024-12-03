import { Box } from '@mui/material'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'
import { StyledBaseWrapper } from './BaseWrapper.style'
import { Outlet } from 'react-router-dom'
import { Suspense, useState } from 'react'
import { CustomLoader } from '../CustomLoader'
import { useTranslation } from 'react-i18next'
import { useClearError } from '@/hooks/useClearError'
import { useUser } from '@/hooks/useUser'
import { useHandleAuthRedirect } from '@/hooks/useHandleAuthRedirect'
import { CustomAlert } from '../CustomAlert/CustomAlert'

const loaderText = 'common.loading'

export const BaseWrapper = () => {
  useClearError()
  const { t } = useTranslation()
  const { isAuthenticated, isAuthFailed, setIsAuthFailed } = useUser()
  const [isAlertOpen, setAlertOpen] = useState(false)

  const handleAuthFailed = () => {
    setAlertOpen(true)
    setIsAuthFailed(false)
  }

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
