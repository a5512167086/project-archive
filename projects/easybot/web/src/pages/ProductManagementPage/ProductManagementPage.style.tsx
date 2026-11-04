import { Container, styled } from '@mui/material'

export const StyledProductManagementPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  boxSizing: 'border-box',
  overflow: 'hidden',
  minHeight: 0,
  paddingBottom: '16px',
  '& .product__titleBox': {
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0
  },
  '& .product__title': {
    fontSize: '2rem',
    fontWeight: '500'
  },
  '& .product__tableContainer': {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    minHeight: 0
  },
  // Tabs container
  '& .MuiTabs-root': {
    flexShrink: 0
  }
}))
