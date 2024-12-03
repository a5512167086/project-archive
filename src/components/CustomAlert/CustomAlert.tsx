import { Alert, Snackbar } from '@mui/material'
import { CustomAlertProps } from './CustomAlert.type'
export const CustomAlert = ({
  open,
  message,
  severity = 'warning',
  onClose
}: CustomAlertProps) => {
  return (
    <Snackbar open={open} autoHideDuration={5000} onClose={onClose}>
      <Alert onClose={onClose} severity={severity}>
        {message}
      </Alert>
    </Snackbar>
  )
}
