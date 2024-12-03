import { Box, styled } from '@mui/material'

export const StyledNotFoundPage = styled(Box)(() => ({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  textAlign: 'center',
  width: '100%',
  height: '100vh',
  '& .notfound__errorImg': {
    maxWidth: '300px',
    margin: '20px 0'
  },
  '& .notfound__title': {
    margin: '10px 0 ',
    fontSize: '2.25rem',
    fontWeight: 'bold'
  }
}))
