import { Box } from '@mui/material'
import { styled } from '@mui/material/styles'

export const StyledDivider = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  width: '100%',
  marginTop: theme.spacing(1),
  marginBottom: theme.spacing(1),
  '& .divider__line': {
    flexGrow: 1,
    borderBottom: '2px solid lightgray'
  },
  '& .divider__text': {
    paddingRight: theme.spacing(2),
    paddingLeft: theme.spacing(2),
    fontWeight: 500,
    fontSize: 22
  }
}))
