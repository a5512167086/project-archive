import { Button, Paper } from '@mui/material'
import { styled } from '@mui/system'

export const UserSettingStyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  marginTop: theme.spacing(4),
  borderRadius: theme.spacing(2)
}))

export const UserSettingStyledButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(1),
  padding: theme.spacing(1.5),
  borderRadius: theme.spacing(1),
  textTransform: 'none',
  fontSize: '1rem',
  width: '100%',
  display: 'flex',
  gap: theme.spacing(1)
}))
