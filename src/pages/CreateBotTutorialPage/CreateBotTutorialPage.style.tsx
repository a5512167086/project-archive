import { styled } from '@mui/material/styles'
import { Container } from '@mui/material'

export const StyledCreateBotTutorialPage = styled(Container)(() => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  '& .tutorial__link': {
    margin: '10px 0',
    textAlign: 'center',
    a: {
      fontSize: '1.5rem',
      textDecoration: 'none',
      color: 'teal'
    }
  },
  '& .tutorial__stepBox': {
    padding: '10px 0',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center'
  },
  '& .tutorial__image': {
    maxWidth: '85%'
  }
}))
