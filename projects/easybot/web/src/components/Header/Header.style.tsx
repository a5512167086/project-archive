import { styled } from '@mui/material/styles'
import { Box } from '@mui/material'

export const StyledHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  height: '64px',
  '& .header__toolbar': {
    height: '100%'
  },
  '& .header__iconButton': {
    marginRight: '20px',
    [theme.breakpoints.up('sm')]: {
      display: 'none'
    }
  },
  '& .header__logo': {
    height: '60px',
    width: '60px',
    '& path': {
      fill: `${theme.palette.common.white} !important`
    },
    [theme.breakpoints.down('sm')]: {
      display: 'none'
    }
  },
  '& .header__title': {
    flexGrow: 1,
    fontSize: '1.75rem',
    [theme.breakpoints.down('sm')]: {
      textAlign: 'center',
      paddingRight: '45px'
    },
    [theme.breakpoints.up('sm')]: {
      display: 'block'
    }
  },
  '& .header__navBox': {
    [theme.breakpoints.down('sm')]: {
      display: 'none'
    },
    [theme.breakpoints.up('sm')]: {
      display: 'block'
    }
  },
  '& .header__navLink': {
    color: theme.palette.common.white
  },
  
}))
