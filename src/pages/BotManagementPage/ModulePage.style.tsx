import { styled } from '@mui/material/styles'
import { Container } from '@mui/material'

export const StyledBotManagementPage = styled(Container)(() => ({
  '& .bot__title': {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    margin: '10px 0 20px'
  }
}))
