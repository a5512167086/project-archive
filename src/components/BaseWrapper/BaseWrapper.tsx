import { Box } from '@mui/material'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'
import { StyledBaseWrapper } from './BaseWrapper.style'
import { Outlet } from 'react-router-dom'
import { Suspense, useEffect, useState, useCallback } from 'react'
import { CustomLoader } from '../CustomLoader'
import { useTranslation } from 'react-i18next'
import { useUser } from '@/hooks/useUser'
import { useHandleAuthRedirect } from '@/hooks/useHandleAuthRedirect'
import { CustomAlert } from '../CustomAlert/CustomAlert'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { useApiErrorHandler } from '@/hooks/useApiErrorHandler'
import { clearBotError } from '@/store/modules/botSlice'
import { clearUserError } from '@/store/modules/userSlice'
import { clearModuleError } from '@/store/modules/moduleSlice'
import { clearKnowledgeError } from '@/store/modules/knowledgeSlice'
import { clearReservationError } from '@/store/modules/reservationSlice'

const loaderText = 'common.loading'

export const BaseWrapper = () => {
  const dispatch = useAppDispatch()
  const { t } = useTranslation()
  const { handleError } = useApiErrorHandler()
  const { isAuthFailed, setIsAuthFailed } = useUser()
  const { errorCode: botErrorCode } = useAppSelector((state) => state.bot)
  const { isAuthenticated, errorCode: userErrorCode } = useAppSelector(
    (state) => state.user
  )
  const { errorCode: moduleError } = useAppSelector((state) => state.module)
  const { errorCode: knowledgeError } = useAppSelector(
    (state) => state.knowledge
  )
  const { errorCode: reservationError } = useAppSelector(
    (state) => state.reservation
  )
  const [isAlertOpen, setAlertOpen] = useState(false)

  const handleAuthFailed = useCallback(() => {
    setAlertOpen(true)
    setIsAuthFailed(false)
  }, [setIsAuthFailed])

  const handleErrorNotification = useCallback(
    (errorCode: string | null, clearAction?: () => void) => {
      if (errorCode) {
        handleError({ error_code: errorCode })
        if (clearAction) clearAction()
      }
    },
    [handleError]
  )

  useHandleAuthRedirect(isAuthenticated, isAuthFailed, handleAuthFailed)

  useEffect(() => {
    handleErrorNotification(botErrorCode, () => dispatch(clearBotError()))
    handleErrorNotification(userErrorCode, () => dispatch(clearUserError()))
    handleErrorNotification(moduleError, () => dispatch(clearModuleError()))
    handleErrorNotification(knowledgeError, () =>
      dispatch(clearKnowledgeError())
    )
    handleErrorNotification(reservationError, () =>
      dispatch(clearReservationError())
    )
  }, [
    botErrorCode,
    userErrorCode,
    moduleError,
    knowledgeError,
    reservationError,
    handleErrorNotification,
    dispatch
  ])
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
