import { styled } from '@mui/material/styles'
import { Drawer } from '@mui/material'

export const StyledDrawer = styled(Drawer)(({ theme }) => ({
  [theme.breakpoints.up('sm')]: {
    display: 'none'
  },
  '& .MuiDrawer-paper': {
    boxSizing: 'border-box',
    width: '240px'
  },
  '& .drawer__box': {
    textAlign: 'center'
  },
  '& .drawer__listButton': {
    textAlign: 'center'
  },
  '& .drawer__languageChangerBox': {
    width: '100%',
    display: 'flex',
    justifyContent: 'center'
  }
}))
