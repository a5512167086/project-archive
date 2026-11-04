import { enqueueSnackbar } from 'notistack'
import { ERROR_CODE_MESSAGE_MAPPING } from '@/configs/common'
import { TFunction } from 'i18next'

export interface ApiError {
  error_code: string
  error_message: string
}

export const showErrorToast = (
  errorCode: unknown,
  t: TFunction,
  customMessage?: string
) => {
  console.log('showErrorToast errorCode:', errorCode)
  const errorMessage =
    errorCode &&
    ERROR_CODE_MESSAGE_MAPPING[
      errorCode as keyof typeof ERROR_CODE_MESSAGE_MAPPING
    ]
      ? t(
          ERROR_CODE_MESSAGE_MAPPING[
            errorCode as keyof typeof ERROR_CODE_MESSAGE_MAPPING
          ]
        )
      : customMessage
        ? t(customMessage)
        : t('error.unknown_error')

  enqueueSnackbar(errorMessage, {
    variant: 'error',
    preventDuplicate: true,
    autoHideDuration: 5000
  })
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
