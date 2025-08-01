import { styled } from '@mui/material/styles'
import { Typography, Paper, Container } from '@mui/material'

export const StyledEcommSettingPage = styled(Container)(() => ({
  width: '100%'
}))

export const Title = styled(Typography)(({ theme }) => ({
  fontSize: '2rem',
  fontWeight: 'bold',
  marginBottom: theme.spacing(2)
}))

export const SectionTitle = styled(Typography)({
  fontSize: '1.25rem',
  fontWeight: '600'
})

export const ShippingOptionCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(2),
  transition: 'box-shadow 0.3s',
  '&:hover': {
    boxShadow: theme.shadows[4]
  },
  '& .method-name': {
    fontWeight: 500,
    flexGrow: 1
  },
  '& .fee-input': {
    width: '120px'
  }
}))
