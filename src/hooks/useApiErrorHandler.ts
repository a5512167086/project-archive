import { useTranslation } from 'react-i18next'
import {
  handleApiError,
  showSuccessToast,
  showInfoToast,
  showWarningToast,
  withErrorHandling
} from '@/utils/errorHandler'

/**
 * Custom hook for API error handling with toast notifications
 */
export const useApiErrorHandler = () => {
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

  const wrapApiCall = <T extends unknown[], R>(
    apiCall: (...args: T) => Promise<R>,
    options?: {
      customErrorMessage?: string
      showSuccessMessage?: string
      onError?: (error: unknown) => void
      onSuccess?: (result: R) => void
    }
  ) => {
    return withErrorHandling(apiCall, t, options)
  }

  return {
    handleError,
    showSuccess,
    showInfo,
    showWarning,
    wrapApiCall
  }
}
