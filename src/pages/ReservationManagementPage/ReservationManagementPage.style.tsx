import { Container, styled } from '@mui/material'

export const StyledReservationManagementPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  height: '80vh',
  boxSizing: 'border-box',
  '& .reservation__title': {
    fontSize: '2rem',
    fontWeight: '500'
  }
}))
