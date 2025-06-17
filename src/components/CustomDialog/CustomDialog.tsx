import { useState } from 'react'
import {
  Box,
  Button,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  FormControlLabel,
  Checkbox,
  IconButton,
  Typography,
  MenuItem
} from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import { useTranslation } from 'react-i18next'
import { TimePicker } from '@mui/x-date-pickers/TimePicker'
import dayjs, { Dayjs } from 'dayjs'
import { CustomDialogProps } from './CustomDialog.type'
import { CustomLoader } from '../CustomLoader'
import { CustomLink } from '../CustomLink'
import { StyledDialog, VisuallyHiddenInput } from './CustomDialog.style'
import { FieldProps } from './CustomDialog.type'

const dialogContent = {
  cancel: 'common.cancel',
  done: 'common.done'
}

export const CustomDialog = <T extends Record<string, unknown>>({
  handleClose,
  fields = [],
  title,
  linkText,
  link,
  dangerButton,
  onSubmit,
  maxWidth,
  ...rest
}: Omit<CustomDialogProps<T>, 'onSubmit'> & {
  onSubmit: (data: T) => void
}) => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [arrayState, setArrayState] = useState<
    Record<string, Record<string, unknown>[]>
  >({})
  const [timeValues, setTimeValues] = useState<Record<string, Dayjs | null>>({})
  const [checkboxValues, setCheckboxValues] = useState<Record<string, boolean>>(
    {}
  )
  const [formState, setFormState] = useState<Record<string, unknown>>({})

  const validateField = (
    field: FieldProps,
    value: string | File | null
  ): string | undefined => {
    if (!field.required && !value) return undefined
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

  const handleFieldBlur = (field: FieldProps, value: string | File | null) => {
    const error = validateField(field, value)
    setErrors((prevErrors) => ({ ...prevErrors, [field.name]: error || '' }))
  }

  const handleDialogClose = () => {
    setErrors({})
    setArrayState({})
    setTimeValues({})
    setCheckboxValues({})
    setFormState({})
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
      } else if (field.type === 'array') {
        formJson[field.name] = arrayState[field.name] || []
      } else if (field.type === 'time') {
        formJson[field.name] = timeValues[field.name]?.format('HH:mm') || ''
      } else if (field.type === 'checkbox') {
        formJson[field.name] = checkboxValues[field.name] || false
      } else {
        formJson[field.name] = formState[field.name] ?? ''
      }
    })

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
      await onSubmit(formJson as T)
    } finally {
      setLoading(false)
      handleDialogClose()
    }
  }

  return (
    <StyledDialog
      onClose={handleDialogClose}
      fullWidth
      maxWidth={maxWidth}
      PaperProps={{ component: 'form', onSubmit: handleSubmit }}
      {...rest}
    >
      <DialogTitle textAlign="center" variant="h5">
        {t(title)}
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {fields.map((field) => {
          if (field.type === 'file') {
            return (
              <Button
                key={field.id}
                component="label"
                variant="contained"
                startIcon={<CloudUploadIcon />}
              >
                {field.name}
                <VisuallyHiddenInput
                  type="file"
                  name={field.name}
                  onChange={(e) =>
                    handleFieldBlur(field, e.target.files?.[0] || null)
                  }
                />
              </Button>
            )
          }

          if (field.type === 'array') {
            const items = arrayState[field.name] || []
            return (
              <Box key={field.id}>
                <Box
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                >
                  <Typography fontWeight="bold">{t(field.label)}</Typography>
                  <IconButton
                    onClick={() => {
                      const newItem = (field.fields ?? []).reduce(
                        (acc: Record<string, unknown>, f: FieldProps) => ({
                          ...acc,
                          [f.name]: ''
                        }),
                        {}
                      )
                      const next = [...items, newItem]
                      setArrayState((prev) => ({ ...prev, [field.name]: next }))
                    }}
                  >
                    <AddIcon />
                  </IconButton>
                </Box>
                {items.map((item, idx) => (
                  <Box
                    key={idx}
                    display="flex"
                    gap={1}
                    alignItems="center"
                    flexWrap="wrap"
                    width="100%"
                  >
                    {(field.fields ?? []).map((subField: FieldProps) => {
                      const key = `${field.name}[${idx}].${subField.name}`
                      const value = item[subField.name] ?? ''

                      if (subField.type === 'time') {
                        return (
                          <TimePicker
                            key={key}
                            label={t(subField.label)}
                            value={
                              item[subField.name]
                                ? dayjs(item[subField.name] as string, 'HH:mm')
                                : null
                            }
                            onChange={(newValue) => {
                              const next = [...items]
                              next[idx][subField.name] =
                                newValue?.format('HH:mm') || ''
                              setArrayState((prev) => ({
                                ...prev,
                                [field.name]: next
                              }))
                            }}
                            slotProps={{
                              textField: {
                                variant: 'outlined',
                                margin: 'dense',
                                size: 'small'
                              }
                            }}
                          />
                        )
                      }

                      if (subField.type === 'checkbox') {
                        return (
                          <FormControlLabel
                            key={key}
                            control={
                              <Checkbox
                                checked={!!item[subField.name]}
                                onChange={(e) => {
                                  const next = [...items]
                                  next[idx][subField.name] = e.target.checked
                                  setArrayState((prev) => ({
                                    ...prev,
                                    [field.name]: next
                                  }))
                                }}
                              />
                            }
                            label={t(subField.label)}
                          />
                        )
                      }

                      if (subField.type === 'select') {
                        return (
                          <TextField
                            key={key}
                            select
                            sx={{ minWidth: 120 }}
                            label={t(subField.label)}
                            value={value}
                            onChange={(e) => {
                              const next = [...items]
                              next[idx][subField.name] = e.target.value
                              setArrayState((prev) => ({
                                ...prev,
                                [field.name]: next
                              }))
                            }}
                            size="small"
                            variant="outlined"
                            margin="dense"
                          >
                            <MenuItem value="">請選擇</MenuItem>
                            {(subField.options ?? []).map((opt) => (
                              <MenuItem key={opt.value} value={opt.value}>
                                {opt.label}
                              </MenuItem>
                            ))}
                          </TextField>
                        )
                      }

                      return (
                        <TextField
                          key={key}
                          label={t(subField.label)}
                          value={value as string}
                          onChange={(e) => {
                            const next = [...items]
                            next[idx][subField.name] = e.target.value
                            setArrayState((prev) => ({
                              ...prev,
                              [field.name]: next
                            }))
                          }}
                          size="small"
                          variant="outlined"
                          margin="dense"
                        />
                      )
                    })}
                    <IconButton
                      onClick={() => {
                        const next = [...items]
                        next.splice(idx, 1)
                        setArrayState((prev) => ({
                          ...prev,
                          [field.name]: next
                        }))
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            )
          }

          if (field.type === 'select') {
            return (
              <TextField
                key={field.id}
                required={field.required}
                margin="dense"
                id={field.id}
                name={field.name}
                label={t(field.label)}
                value={(formState[field.name] as string) ?? ''}
                onChange={(e) => {
                  const value = e.target.value
                  setFormState((prev) => ({ ...prev, [field.name]: value }))
                }}
                select
                fullWidth
                variant="outlined"
                error={!!errors[field.name]}
                helperText={errors[field.name]}
              >
                <MenuItem value="">請選擇</MenuItem>
                {(field.options ?? []).map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </TextField>
            )
          }

          if (field.type === 'checkbox') {
            return (
              <FormControlLabel
                key={field.id}
                control={
                  <Checkbox
                    name={field.name}
                    checked={checkboxValues[field.name] || false}
                    onChange={(e) => {
                      setCheckboxValues((prev) => ({
                        ...prev,
                        [field.name]: e.target.checked
                      }))
                    }}
                  />
                }
                label={t(field.label)}
              />
            )
          }

          if (field.type === 'time') {
            return (
              <TimePicker
                key={field.id}
                ampm={false}
                label={t(field.label)}
                value={timeValues[field.name] || null}
                onChange={(newValue) => {
                  setTimeValues((prev) => ({
                    ...prev,
                    [field.name]: newValue
                  }))
                }}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    error: !!errors[field.name],
                    helperText: errors[field.name]
                  }
                }}
              />
            )
          }

          return (
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
              value={(formState[field.name] as string) ?? ''}
              onChange={(e) => {
                const value = e.target.value
                setFormState((prev) => ({ ...prev, [field.name]: value }))
              }}
              onBlur={(e) => handleFieldBlur(field, e.target.value)}
            />
          )
        })}
      </DialogContent>
      <DialogActions>
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
            className="dialog__actionButton"
          >
            {t(dialogContent.cancel)}
          </Button>
          <Button
            type="submit"
            variant="contained"
            color={dangerButton ? 'error' : 'success'}
            className="dialog__actionButton"
            disabled={loading}
          >
            {loading ? <CustomLoader size={24} /> : t(dialogContent.done)}
          </Button>
        </Box>
      </DialogActions>
    </StyledDialog>
  )
}
