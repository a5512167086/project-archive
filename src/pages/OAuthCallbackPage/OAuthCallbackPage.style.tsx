import { Box, styled } from '@mui/material'

export const StyledOAuthCallbackPage = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  textAlign: 'center',
  width: '100%',
  height: '100vh',
  [theme.breakpoints.down('sm')]: {
    padding: '10px'
  },
  '& .oauth__paper': {
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    backgroundColor: 'background.paper'
  },
  '& .oauth__icon': {
    fontSize: '3.5rem',
    marginBottom: '15px'
  },
  '& .oauth__text': {
    marginBottom: '15px'
  },
  '& .oauth__button': {
    margin: '10px 0'
  }
}))
