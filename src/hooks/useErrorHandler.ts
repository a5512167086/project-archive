import { useEffect, useCallback } from 'react'
import { showErrorToast } from '@/utils/toast'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { clearBotError } from '@/store/modules/botSlice'
import { clearUserError } from '@/store/modules/userSlice'
import { clearModuleError } from '@/store/modules/moduleSlice'
import { clearKnowledgeError } from '@/store/modules/knowledgeSlice'
import { clearReservationError } from '@/store/modules/reservationSlice'
import { clearBrandError } from '@/store/modules/brandSlice'
import { useTranslation } from 'react-i18next'

export const useErrorHandler = (options?: {
  autoHandle?: boolean
  excludeSlices?: string[]
}) => {
  const { autoHandle = true, excludeSlices = [] } = options || {}
  const dispatch = useAppDispatch()
  const { t } = useTranslation()
  
  // 取得所有 slice 的錯誤狀態
  const { errorCode: botErrorCode } = useAppSelector((state) => state.bot)
  const { errorCode: userErrorCode } = useAppSelector((state) => state.user)
  const { errorCode: moduleError } = useAppSelector((state) => state.module)
  const { errorCode: knowledgeError } = useAppSelector(
    (state) => state.knowledge
  )
  const { errorCode: reservationError } = useAppSelector(
    (state) => state.reservation
  )
  const { errorCode: brandError } = useAppSelector((state) => state.brand)

  const handleErrorNotification = useCallback(
    (errorCode: string | null, clearAction?: () => void) => {
      if (errorCode) {
        console.log('handleErrorNotification - Processing error:', errorCode)
        try {
          showErrorToast(errorCode, t)
          console.log('handleErrorNotification - Toast shown successfully')
          if (clearAction) {
            clearAction()
            console.log('handleErrorNotification - Error cleared')
          }
        } catch (error) {
          console.error('handleErrorNotification - Error showing toast:', error)
        }
      }
    },
    [t]
  )

  // 手動處理單一錯誤的函數
  const handleSingleError = useCallback(
    (sliceName: string, errorCode: string | null) => {
      if (!errorCode) return

      const clearActions = {
        bot: () => dispatch(clearBotError()),
        user: () => dispatch(clearUserError()),
        module: () => dispatch(clearModuleError()),
        knowledge: () => dispatch(clearKnowledgeError()),
        reservation: () => dispatch(clearReservationError()),
        brand: () => dispatch(clearBrandError())
      }

      const clearAction = clearActions[sliceName as keyof typeof clearActions]
      handleErrorNotification(errorCode, clearAction)
    },
    [handleErrorNotification, dispatch]
  )

  // 為每個錯誤類型創建單獨的 useEffect，確保能捕捉到瞬間的錯誤
  useEffect(() => {
    if (autoHandle && botErrorCode && !excludeSlices.includes('bot')) {
      console.log('Bot error detected:', botErrorCode)
      handleErrorNotification(botErrorCode, () => dispatch(clearBotError()))
    }
  }, [botErrorCode, autoHandle, excludeSlices, handleErrorNotification, dispatch])

  useEffect(() => {
    if (autoHandle && userErrorCode && !excludeSlices.includes('user')) {
      console.log('User error detected:', userErrorCode)
      handleErrorNotification(userErrorCode, () => dispatch(clearUserError()))
    }
  }, [userErrorCode, autoHandle, excludeSlices, handleErrorNotification, dispatch])

  useEffect(() => {
    if (autoHandle && moduleError && !excludeSlices.includes('module')) {
      console.log('Module error detected:', moduleError)
      handleErrorNotification(moduleError, () => dispatch(clearModuleError()))
    }
  }, [moduleError, autoHandle, excludeSlices, handleErrorNotification, dispatch])

  useEffect(() => {
    if (autoHandle && knowledgeError && !excludeSlices.includes('knowledge')) {
      console.log('Knowledge error detected:', knowledgeError)
      handleErrorNotification(knowledgeError, () => dispatch(clearKnowledgeError()))
    }
  }, [knowledgeError, autoHandle, excludeSlices, handleErrorNotification, dispatch])

  useEffect(() => {
    if (autoHandle && reservationError && !excludeSlices.includes('reservation')) {
      console.log('Reservation error detected:', reservationError)
      handleErrorNotification(reservationError, () => dispatch(clearReservationError()))
    }
  }, [reservationError, autoHandle, excludeSlices, handleErrorNotification, dispatch])

  useEffect(() => {
    if (autoHandle && brandError && !excludeSlices.includes('brand')) {
      console.log('Brand error detected:', brandError)
      handleErrorNotification(brandError, () => dispatch(clearBrandError()))
    }
  }, [brandError, autoHandle, excludeSlices, handleErrorNotification, dispatch])

  return { handleSingleError }
}
