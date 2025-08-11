import { styled } from '@mui/material/styles'
import { Container } from '@mui/material'

export const StyledSignUpPage = styled(Container)(({ theme }) => ({
  '& .signup__box': {
    marginTop: 8,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  },
  '& .signup__avatar': {
    margin: '10px',
    backgroundColor: theme.palette.primary.main
  },
  '& .signup__formBox': {
    marginTop: '10px'
  }
}))
