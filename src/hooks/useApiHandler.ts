import { useTranslation } from 'react-i18next'
import {
  handleApiError,
  showSuccessToast,
  showInfoToast,
  showWarningToast
} from '@/utils/errorHandler'

/**
 * Custom hook for API error handling with toast notifications
 */
export const useApiHandler = () => {
  const { t } = useTranslation()

  const handleError = (error: unknown, customMessage?: string) => {
    return handleApiError(error, t, customMessage)
  }

  const showSuccess = (message: string) => {
    showSuccessToast(message, t)
  }

  const showInfo = (message: string) => {
    showInfoToast(message, t)
  }

  const showWarning = (message: string) => {
    showWarningToast(message, t)
  }

  return {
    handleError,
    showSuccess,
    showInfo,
    showWarning
  }
}
