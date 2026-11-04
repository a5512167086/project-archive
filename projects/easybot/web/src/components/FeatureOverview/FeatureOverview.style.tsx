import { styled } from '@mui/material/styles'
import { Container } from '@mui/material'

export const StyledFeatureOverview = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  '& .overview__title': {
    textAlign: 'center',
    margin: '20px 0',
    fontSize: '2rem',
    fontWeight: 'bold'
  },
  '& .overview__cardBox': {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between'
  }
}))
