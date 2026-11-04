import { styled } from '@mui/material/styles'
import { Box } from '@mui/material'

export const StyledFooter = styled(Box)(({ theme }) => ({
  width: '100%',
  padding: '10px 0',
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.common.white,
  textAlign: 'center'
}))
