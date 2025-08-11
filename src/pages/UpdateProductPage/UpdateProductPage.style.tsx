import { Container, styled } from '@mui/material'

export const StyledUpdateProductPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  height: 'calc(100vh - 64px)', // 100vh 減去 header 高度
  boxSizing: 'border-box',
  overflow: 'hidden', // 防止頁面滾動
  paddingBottom: '20px', // 添加底部邊距
  '& .MuiCard-root': {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  '& .MuiCardContent-root': {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto' // Allow scrolling within card content
  }
}))