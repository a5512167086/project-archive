import { useEffect, useCallback } from 'react'
import { showErrorToast } from '@/utils/toast'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { useTranslation } from 'react-i18next'

// 匯入清除錯誤的 actions
import { clearBotError } from '@/store/modules/botSlice'
import { clearUserError } from '@/store/modules/userSlice'
import { clearModuleError } from '@/store/modules/moduleSlice'
import { clearKnowledgeError } from '@/store/modules/knowledgeSlice'
import { clearReservationError } from '@/store/modules/reservationSlice'
import { clearBrandError } from '@/store/modules/brandSlice'
import { clearCategoryError } from '@/store/modules/categorySlice'
import { clearEcommError } from '@/store/modules/ecommSlice'

export const useErrorHandler = (options?: {
  autoHandle?: boolean
  excludeSlices?: string[]
}) => {
  const { autoHandle = true, excludeSlices = [] } = options || {}
  const dispatch = useAppDispatch()
  const { t } = useTranslation()

  // 收集所有 slice 的錯誤
  const errorStates = useAppSelector((state) => ({
    bot: state.bot.errorCode,
    user: state.user.errorCode,
    module: state.module.errorCode,
    knowledge: state.knowledge.errorCode,
    reservation: state.reservation.errorCode,
    brand: state.brand.errorCode,
    category: state.category.errorCode,
    ecomm: state.ecomm.errorCode
  }))

  // 對應每個 slice 的清除 action
  const clearActions: Record<string, () => void> = {
    bot: () => dispatch(clearBotError()),
    user: () => dispatch(clearUserError()),
    module: () => dispatch(clearModuleError()),
    knowledge: () => dispatch(clearKnowledgeError()),
    reservation: () => dispatch(clearReservationError()),
    brand: () => dispatch(clearBrandError()),
    category: () => dispatch(clearCategoryError()),
    ecomm: () => dispatch(clearEcommError())
  }

  // 顯示錯誤通知並清除
  const handleErrorNotification = useCallback(
    (errorCode: string | null, clearAction?: () => void) => {
      if (errorCode) {
        console.log('handleErrorNotification - Processing error:', errorCode)
        try {
          showErrorToast(errorCode, t)
          console.log('handleErrorNotification - Toast shown successfully')
          clearAction?.()
          console.log('handleErrorNotification - Error cleared')
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
      const clearAction = clearActions[sliceName]
      handleErrorNotification(errorCode, clearAction)
    },
    [clearActions, handleErrorNotification]
  )

  // 單一 useEffect 處理所有 slice 錯誤
  useEffect(() => {
    if (!autoHandle) return

    for (const [sliceName, errorCode] of Object.entries(errorStates)) {
      if (errorCode && !excludeSlices.includes(sliceName)) {
        console.log(`${sliceName} error detected:`, errorCode)
        const clearAction = clearActions[sliceName]
        handleErrorNotification(errorCode, clearAction)
      }
    }
  }, [
    autoHandle,
    excludeSlices,
    errorStates,
    clearActions,
    handleErrorNotification
  ])

  return { handleSingleError }
}
