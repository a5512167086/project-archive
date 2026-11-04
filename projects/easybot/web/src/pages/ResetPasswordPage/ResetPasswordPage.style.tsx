import { Container, styled } from '@mui/material'

export const StyledResetPasswordPage = styled(Container)(({ theme }) => ({
  '& .reset__box': {
    marginTop: 8,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  },
  '& .reset__avatar': {
    margin: '10px',
    backgroundColor: theme.palette.primary.main
  },
  '& .reset__description': {
    marginTop: '10px',
    textAlign: 'center'
  },
  '& .reset__formBox': {
    marginTop: '10px',
    width: '100%'
  },
  '& .reset__resetButton': {
    margin: '20px 0'
  }
}))
