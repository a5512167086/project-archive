import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import { CustomDialogProps } from './CustomDialog.type'
import { StyledDialog, VisuallyHiddenInput } from './CustomDialog.style'
import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import { CustomLoader } from '../CustomLoader'
import { Box } from '@mui/material'
import { CustomLink } from '../CustomLink'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'

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

  const validateField = (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    field: any,
    value: string | File | null
  ): string | undefined => {
    if (!field.required && !value) {
      return undefined
    }
    if (
      field.type === 'text' &&
      field.validate &&
      !field.validate(value as string)
    ) {
      return field.errorText?.invalidFormat || t('error.invalidFormat')
    }
    if (field.type === 'file' && field.required && !value) {
      return t('error.fileRequired')
    }
    return undefined
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleFieldBlur = (field: any, value: string | File | null) => {
    const error = validateField(field, value)
    setErrors((prevErrors) => ({
      ...prevErrors,
      [field.name]: error || ''
    }))
  }

  const handleDialogClose = () => {
    setErrors({})
    handleClose()
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)

    const formData = new FormData(event.currentTarget)
    const formJson: Record<string, unknown> = {}

    fields.forEach((field) => {
      if (field.type === 'file') {
        formJson[field.name] = formData.get(field.name)
      } else {
        formJson[field.name] = formData.get(field.name) as string
      }
    })
    console.log(formJson)

    const validatedData = formJson as T

    const newErrors: Record<string, string> = {}
    fields.forEach((field) => {
      const error = validateField(
        field,
        formJson[field.name] as string | File | null
      )
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
          fields.map((field) =>
            field.type === 'file' ? (
              <Button
                key={field.id}
                component="label"
                variant="contained"
                className="dialog__uploadButton"
                startIcon={<CloudUploadIcon />}
              >
                {field.name}
                <VisuallyHiddenInput
                  type="file"
                  multiple={false}
                  key={field.id}
                  required={field.required}
                  id={field.id}
                  name={field.name}
                  onChange={(e) => {
                    const file = e.target.files?.[0] || null
                    handleFieldBlur(field, file)
                  }}
                />
              </Button>
            ) : (
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
            )
          )}
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
