import { enqueueSnackbar } from 'notistack'
import { TFunction } from 'i18next'
import { ERROR_CODE_MESSAGE_MAPPING } from '@/configs/common'

export interface ApiError {
  error_code: string
  error_message: string
}

/**
 * Handles API errors by showing toast notifications
 * @param error - The error object from API response
 * @param t - Translation function
 * @param customMessage - Optional custom message to override default
 */
export const handleApiError = (
  error: unknown,
  t: TFunction,
  customMessage?: string
) => {
  let errorCode = 'UNKNOWN_ERROR'
  let errorMessage = customMessage || t('error.unknown_error')

  // Handle RTK Query error format
  if (error && typeof error === 'object' && 'data' in error) {
    const rtkError = error as { data: ApiError }
    const apiError = rtkError.data
    if (apiError?.error_code) {
      errorCode = apiError.error_code
      errorMessage = t(
        ERROR_CODE_MESSAGE_MAPPING[
          errorCode as keyof typeof ERROR_CODE_MESSAGE_MAPPING
        ] || 'error.unknown_error'
      )
    }
  }

  // Handle other error formats
  else if (error && typeof error === 'object' && 'error_code' in error) {
    const apiError = error as ApiError
    errorCode = apiError.error_code
    errorMessage = t(
      ERROR_CODE_MESSAGE_MAPPING[
        errorCode as keyof typeof ERROR_CODE_MESSAGE_MAPPING
      ] || 'error.unknown_error'
    )
  }

  enqueueSnackbar(errorMessage, {
    variant: 'error',
    preventDuplicate: true,
    autoHideDuration: 5000
  })

  return { errorCode, errorMessage }
}

/**
 * Shows a success toast notification
 * @param message - Success message key or direct message
 * @param t - Translation function
 */
export const showSuccessToast = (message: string, t: TFunction) => {
  enqueueSnackbar(t(message), {
    variant: 'success',
    preventDuplicate: true,
    autoHideDuration: 3000
  })
}

/**
 * Shows an info toast notification
 * @param message - Info message key or direct message
 * @param t - Translation function
 */
export const showInfoToast = (message: string, t: TFunction) => {
  enqueueSnackbar(t(message), {
    variant: 'info',
    preventDuplicate: true,
    autoHideDuration: 4000
  })
}

/**
 * Shows a warning toast notification
 * @param message - Warning message key or direct message
 * @param t - Translation function
 */
export const showWarningToast = (message: string, t: TFunction) => {
  enqueueSnackbar(t(message), {
    variant: 'warning',
    preventDuplicate: true,
    autoHideDuration: 4000
  })
}

/**
 * Higher-order function that wraps API calls with automatic error handling
 * @param apiCall - The API call function
 * @param t - Translation function
 * @param options - Optional configuration
 */
export const withErrorHandling = <T extends unknown[], R>(
  apiCall: (...args: T) => Promise<R>,
  t: TFunction,
  options?: {
    customErrorMessage?: string
    showSuccessMessage?: string
    onError?: (error: unknown) => void
    onSuccess?: (result: R) => void
  }
) => {
  return async (...args: T): Promise<R | undefined> => {
    try {
      const result = await apiCall(...args)

      if (options?.showSuccessMessage) {
        showSuccessToast(options.showSuccessMessage, t)
      }

      if (options?.onSuccess) {
        options.onSuccess(result)
      }

      return result
    } catch (error) {
      handleApiError(error, t, options?.customErrorMessage)

      if (options?.onError) {
        options.onError(error)
      }

      // Re-throw to allow caller to handle if needed
      throw error
    }
  }
}
