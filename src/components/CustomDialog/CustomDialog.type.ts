import { DialogProps } from '@mui/material'

export type FieldType =
  | 'text'
  | 'number'
  | 'file'
  | 'select'
  | 'time'
  | 'checkbox'
  | 'array'
  | 'password'
  | 'multi-select'

export interface FieldProps {
  id: string
  name: string
  label: string
  type: FieldType
  required?: boolean
  options?: { value: string | number; label: string }[]
  fields?: FieldProps[]
  validate?: (val: string) => boolean
  errorText?: {
    invalidFormat?: string
  }
}

export type CustomDialogProps<T = Record<string, unknown>> = DialogProps & {
  handleClose: () => void
  fields?: FieldProps[]
  title: string
  linkText?: string
  link?: string
  dangerButton?: boolean
  onSubmit: (data: T) => void
}
