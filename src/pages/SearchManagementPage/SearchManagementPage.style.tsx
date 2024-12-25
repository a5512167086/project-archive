import { Container, styled } from '@mui/material'

export const StyledSearchManagementPage = styled(Container)(() => ({
  '& .search__titleBox': {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  '& .search__button': {
    marginRight: '10px'
  },
  '& .search__title': {
    fontSize: '2rem',
    fontWeight: '500',
    marginBottom: '20px'
  }
}))
