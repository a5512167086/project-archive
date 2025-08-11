import { Container, styled } from '@mui/material'

export const StyledKnowledgeManagementPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  height: 'calc(100vh - 64px)', // 100vh 減去 header 高度
  boxSizing: 'border-box',
  overflow: 'hidden', // 防止頁面滾動
  paddingBottom: '20px', // 添加底部邊距
  '& .knowledge__titleBox': {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0, // 防止標題區域被壓縮
    marginBottom: '16px'
  },
  '& .knowledge__button': {
    marginRight: '10px'
  },
  '& .knowledge__title': {
    fontSize: '2rem',
    fontWeight: '500'
  }
}))
