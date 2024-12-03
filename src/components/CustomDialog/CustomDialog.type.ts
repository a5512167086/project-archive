interface FieldProps {
  id: string
  name: string
  label: string
  type: string
  required?: boolean
}

export type CustomDialogProps<T = Record<string, unknown>> = {
  isOpen: boolean
  handleClose: () => void
  fields?: FieldProps[]
  title: string
  linkText?: string
  link?: string
  dangerButton?: boolean
  onSubmit: (data: T) => void
}
