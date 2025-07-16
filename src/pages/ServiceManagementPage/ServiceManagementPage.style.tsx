import { Container, styled } from '@mui/material'

export const StyledServiceManagementPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  height: 'calc(100vh - 64px)', // 100vh 減去 header 高度
  boxSizing: 'border-box',
  overflow: 'hidden', // 防止頁面滾動
  paddingBottom: '20px', // 添加底部邊距
  '& .service__titleBox': {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0, // 防止標題區域被壓縮
    marginBottom: '16px'
  },
  '& .service__title': {
    fontSize: '2rem',
    fontWeight: '500'
  },
  '& .service__tableContainer': {
    flex: 1, // 讓表格容器占滿剩餘空間
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    marginBottom: '20px' // 為表格容器添加底部邊距
  }
}))
