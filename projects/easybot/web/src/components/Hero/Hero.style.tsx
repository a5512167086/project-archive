import { styled } from '@mui/material/styles'
import { Box } from '@mui/material'
import { theme } from '@/configs/theme'

export const StyledHero = styled(Box)(() => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  margin: '20px 0',
  [theme.breakpoints.down('md')]: {
    flexWrap: 'wrap-reverse'
  },
  '& .hero__card': {
    display: 'flex', // 讓卡片內的元素使用 flex 排列
    flexDirection: 'column', // 讓圖片和其他元素垂直排列
    maxWidth: '400px',
    height: 'fit-content',
    border: '1px solid lightgray',
    borderRadius: '20px',
    overflow: 'hidden',
    boxShadow: 'rgba(0, 0, 0, 0.1) 0px 10px 50px'
  },
  '& .hero__img': {
    width: '100%',
    height: 'auto', // 確保圖片高度會自動調整以保持比例
    objectFit: 'cover' // 圖片會等比例縮放以填滿容器
  },
  '& .hero__textBox': {
    marginLeft: '20px',
    [theme.breakpoints.down('md')]: {
      margin: '10px 20px',
      textAlign: 'center',
      maxWidth: '480px'
    }
  },
  '& .hero__title': {
    fontSize: '1.75rem',
    fontWeight: 'bold',
    marginBottom: '10px',
    [theme.breakpoints.down('md')]: {
      fontSize: '1.5rem'
    }
  },
  
}))
