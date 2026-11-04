import { useEffect, useCallback, useMemo } from 'react'
import { createSelector } from '@reduxjs/toolkit'
import { showErrorToast } from '@/utils/toast'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { useTranslation } from 'react-i18next'

// actions
import { clearBotError } from '@/store/modules/botSlice'
import { clearUserError } from '@/store/modules/userSlice'
import { clearModuleError } from '@/store/modules/moduleSlice'
import { clearKnowledgeError } from '@/store/modules/knowledgeSlice'
import { clearReservationError } from '@/store/modules/reservationSlice'
import { clearBrandError } from '@/store/modules/brandSlice'
import { clearCategoryError } from '@/store/modules/categorySlice'
import { clearEcommError } from '@/store/modules/ecommSlice'

interface RootState {
  bot: { errorCode: string | null }
  user: { errorCode: string | null }
  module: { errorCode: string | null }
  knowledge: { errorCode: string | null }
  reservation: { errorCode: string | null }
  brand: { errorCode: string | null }
  category: { errorCode: string | null }
  ecomm: { errorCode: string | null }
}

const selectErrorStates = createSelector(
  (state: RootState) => state.bot.errorCode,
  (state: RootState) => state.user.errorCode,
  (state: RootState) => state.module.errorCode,
  (state: RootState) => state.knowledge.errorCode,
  (state: RootState) => state.reservation.errorCode,
  (state: RootState) => state.brand.errorCode,
  (state: RootState) => state.category.errorCode,
  (state: RootState) => state.ecomm.errorCode,
  (bot, user, module, knowledge, reservation, brand, category, ecomm) => ({
    bot,
    user,
    module,
    knowledge,
    reservation,
    brand,
    category,
    ecomm
  })
)

export const useErrorHandler = (options?: {
  autoHandle?: boolean
  excludeSlices?: string[]
}) => {
  const { autoHandle = true, excludeSlices = [] } = options || {}
  const dispatch = useAppDispatch()
  const { t } = useTranslation()

  // ✅ 使用 memoized selector，避免每次都回傳新 {}
  const errorStates = useAppSelector(selectErrorStates)

  // ✅ 2) 用 useMemo 固定 clearActions 參考
  const clearActions = useMemo(
    () => ({
      bot: () => dispatch(clearBotError()),
      user: () => dispatch(clearUserError()),
      module: () => dispatch(clearModuleError()),
      knowledge: () => dispatch(clearKnowledgeError()),
      reservation: () => dispatch(clearReservationError()),
      brand: () => dispatch(clearBrandError()),
      category: () => dispatch(clearCategoryError()),
      ecomm: () => dispatch(clearEcommError())
    }),
    [dispatch]
  )

  const handleErrorNotification = useCallback(
    (errorCode: string | null, clearAction?: () => void) => {
      if (errorCode) {
        try {
          showErrorToast(errorCode, t)
          clearAction?.()
        } catch (error) {
          console.error('handleErrorNotification - Error showing toast:', error)
        }
      }
    },
    [t]
  )

  const handleSingleError = useCallback(
    (sliceName: keyof typeof clearActions, errorCode: string | null) => {
      if (!errorCode) return
      const clearAction = clearActions[sliceName]
      handleErrorNotification(errorCode, clearAction)
    },
    [clearActions, handleErrorNotification]
  )

  useEffect(() => {
    if (!autoHandle) return

    for (const [sliceName, errorCode] of Object.entries(errorStates)) {
      if (errorCode && !excludeSlices.includes(sliceName)) {
        const clearAction = (clearActions as Record<string, () => void>)[
          sliceName
        ]
        handleErrorNotification(errorCode as string, clearAction)
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
