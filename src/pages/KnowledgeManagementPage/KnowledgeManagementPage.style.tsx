import { Container, styled } from '@mui/material'

export const StyledKnowledgeManagementPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  height: '80vh',
  boxSizing: 'border-box',
  '& .knowledge__titleBox': {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  '& .knowledge__button': {
    marginRight: '10px'
  },
  '& .knowledge__title': {
    fontSize: '2rem',
    fontWeight: '500',
  }
}))
