import { styled } from '@mui/material/styles'
import { Box } from '@mui/material'

export const StyledCustomLoader = styled(Box)(() => ({
  flexGrow: 1,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  fontSize: '1.5rem'
}))
