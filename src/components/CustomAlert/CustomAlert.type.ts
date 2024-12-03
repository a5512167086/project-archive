export type CustomAlertProps = {
  open: boolean
  message: string
  severity?: 'success' | 'info' | 'warning' | 'error'
  onClose: () => void
}
