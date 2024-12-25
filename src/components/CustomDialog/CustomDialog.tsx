import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import { CustomDialogProps } from './CustomDialog.type'
import { StyledDialog } from './CustomDialog.style'
import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import { CustomLoader } from '../CustomLoader'
import { Box } from '@mui/material'
import { CustomLink } from '../CustomLink'

const dialogContent = {
  cancel: 'common.cancel',
  done: 'common.done'
}

export const CustomDialog = <T extends Record<string, unknown>>({
  isOpen,
  handleClose,
  fields = [],
  title,
  linkText,
  link,
  dangerButton,
  onSubmit
}: CustomDialogProps<T>) => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const validateField = (field: any, value: string): string | undefined => {
    if (!field.required && !value) {
      return undefined
    }
    if (field.type === 'text' && field.validate && !field.validate(value)) {
      return field.errorText?.invalidFormat || t('error.invalidFormat')
    }
    return undefined
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleFieldBlur = (field: any, value: string) => {
    const error = validateField(field, value)
    setErrors((prevErrors) => ({
      ...prevErrors,
      [field.name]: error || ''
    }))
  }

  const handleDialogClose = () => {
    // 清除所有錯誤
    setErrors({})
    handleClose()
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)

    const formData = new FormData(event.currentTarget)
    const formJson = Object.fromEntries(formData.entries())
    const validatedData = formJson as T

    const newErrors: Record<string, string> = {}
    fields.forEach((field) => {
      const error = validateField(field, formJson[field.name] as string)
      if (error) {
        newErrors[field.name] = error
      }
    })
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      setLoading(false)
      return
    }

    try {
      await onSubmit(validatedData)
    } finally {
      setLoading(false)
      handleDialogClose()
    }
  }

  return (
    <StyledDialog
      maxWidth="xs"
      open={isOpen}
      onClose={handleDialogClose}
      PaperProps={{
        component: 'form',
        onSubmit: handleSubmit
      }}
    >
      <DialogTitle textAlign="center" variant="h5">
        {t(title)}
      </DialogTitle>
      <DialogContent>
        {fields &&
          fields.map((field) => (
            <TextField
              key={field.id}
              required={field.required}
              margin="dense"
              id={field.id}
              name={field.name}
              label={t(field.label)}
              type={field.type}
              fullWidth
              variant="outlined"
              error={!!errors[field.name]}
              helperText={errors[field.name]}
              onBlur={(e) => handleFieldBlur(field, e.target.value)}
            />
          ))}
      </DialogContent>
      <DialogActions className="dialog__actionBox">
        <Box>
          {linkText && link && (
            <CustomLink linkText={t(linkText)} link={link} />
          )}
        </Box>
        <Box>
          <Button
            onClick={!loading ? handleDialogClose : () => {}}
            variant="contained"
            color="primary"
          >
            {t(dialogContent.cancel)}
          </Button>
          <Button
            type="submit"
            variant="contained"
            color={dangerButton ? 'error' : 'success'}
            disabled={loading}
            className="dialog__actionButton"
          >
            {loading ? <CustomLoader size={24} /> : t(dialogContent.done)}
          </Button>
        </Box>
      </DialogActions>
    </StyledDialog>
  )
}
