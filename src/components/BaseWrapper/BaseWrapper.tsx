import { Box } from '@mui/material'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'
import { StyledBaseWrapper } from './BaseWrapper.style'
import { Outlet } from 'react-router-dom'
import { Suspense, useEffect, useState, useCallback } from 'react'
import { CustomLoader } from '../CustomLoader'
import { useTranslation } from 'react-i18next'
import { useClearError } from '@/hooks/useClearError'
import { useUser } from '@/hooks/useUser'
import { useHandleAuthRedirect } from '@/hooks/useHandleAuthRedirect'
import { CustomAlert } from '../CustomAlert/CustomAlert'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { useSnackbar } from 'notistack'
import { ERROR_CODE_MESSAGE_MAPPING } from '@/configs/common'
import { clearBotError } from '@/store/modules/botSlice'
import { clearUserError } from '@/store/modules/userSlice'
import { clearSearchError } from '@/store/modules/searchSlice'
import { clearModuleError } from '@/store/modules/moduleSlice'

const loaderText = 'common.loading'
const unknownError = 'error.unknown_error'

export const BaseWrapper = () => {
  useClearError()
  const dispatch = useAppDispatch()
  const { t } = useTranslation()
  const { enqueueSnackbar } = useSnackbar()
  const { isAuthenticated, isAuthFailed, setIsAuthFailed } = useUser()
  const { errorCode: botErrorCode } = useAppSelector((state) => state.bot)
  const { errorCode: userErrorCode } = useAppSelector((state) => state.user)
  const { errorCode: searchErrorCode } = useAppSelector((state) => state.search)
  const { errorCode: moduleError } = useAppSelector((state) => state.module)
  const [isAlertOpen, setAlertOpen] = useState(false)

  const handleAuthFailed = useCallback(() => {
    setAlertOpen(true)
    setIsAuthFailed(false)
  }, [setIsAuthFailed])

  const handleErrorNotification = useCallback(
    (errorCode: string | null, clearAction?: () => void) => {
      if (errorCode) {
        enqueueSnackbar(
          t(
            ERROR_CODE_MESSAGE_MAPPING[
              errorCode as keyof typeof ERROR_CODE_MESSAGE_MAPPING
            ] || unknownError
          ),
          { variant: 'error' }
        )
        if (clearAction) clearAction()
      }
    },
    [enqueueSnackbar, t]
  )

  useHandleAuthRedirect(isAuthenticated, isAuthFailed, handleAuthFailed)

  useEffect(() => {
    handleErrorNotification(botErrorCode, () => dispatch(clearBotError()))
    handleErrorNotification(userErrorCode, () => dispatch(clearUserError()))
    handleErrorNotification(searchErrorCode, () => dispatch(clearSearchError()))
    handleErrorNotification(moduleError, () => dispatch(clearModuleError()))
  }, [
    botErrorCode,
    userErrorCode,
    searchErrorCode,
    moduleError,
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
