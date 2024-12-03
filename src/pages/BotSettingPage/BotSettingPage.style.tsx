import { styled } from '@mui/material/styles'
import { Container } from '@mui/material'

export const StyledBotSettingPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  '& .setting__title': {
    fontSize: '2rem',
    fontWeight: '500'
  },
  '& .setting__settingBox': {
    width: '85%',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center'
  },
  '& .setting__formBox': {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center'
  },
  '& .setting__dangerBox': {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between'
  }
}))
