import { Container, styled } from '@mui/material'

export const StyledKnowledgeManagementPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  height: 'calc(100vh - 64px)',
  boxSizing: 'border-box',
  overflow: 'hidden',
  paddingBottom: '20px',
  '& .knowledge__titleBox': {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0,
    marginBottom: '16px'
  },
  '& .knowledge__button': {
    marginRight: '10px'
  },
  '& .knowledge__title': {
    fontSize: '2rem',
    fontWeight: '500'
  },
  '& .knowledge__tableContainer': {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    marginBottom: '20px'
  }
}))
