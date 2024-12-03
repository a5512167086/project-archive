import { styled } from '@mui/material/styles'
import { Container } from '@mui/material'

export const StyledBotSettingPage = styled(Container)(({ theme }) => ({
  '& .setting__title': {
    fontSize: '2rem',
    fontWeight: '500'
  },
  '& .setting__settingBox': {
    width: '85%',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'flex-start'
  },
  '& .setting__formBox': {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    '& .setting__textField': {
      width: '35%'
    },
    '& .setting_formButton': {
      width: '100px'
    }
  },
  '& .setting__dangerBox': {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    '& .setting_deleteText': {
      fontWeight: '800',
      color: theme.palette.error.main
    }
  }
}))
