import { styled } from '@mui/material/styles'
import { Card, Switch, SwitchProps } from '@mui/material'

export const StyledSwitch = styled((props: SwitchProps) => (
  <Switch focusVisibleClassName=".Mui-focusVisible" disableRipple {...props} />
))(({ theme }) => ({
  width: 42,
  height: 26,
  padding: 0,
  '& .MuiSwitch-switchBase': {
    padding: 0,
    margin: 2,
    transitionDuration: '300ms',
    '&.Mui-checked': {
      transform: 'translateX(16px)',
      color: '#fff',
      '& + .MuiSwitch-track': {
        backgroundColor: '#65C466',
        opacity: 1,
        border: 0,
        ...theme.applyStyles('dark', {
          backgroundColor: '#2ECA45'
        })
      },
      '&.Mui-disabled + .MuiSwitch-track': {
        opacity: 0.5
      }
    },
    '&.Mui-focusVisible .MuiSwitch-thumb': {
      color: '#33cf4d',
      border: '6px solid #fff'
    },
    '&.Mui-disabled .MuiSwitch-thumb': {
      color: theme.palette.grey[100],
      ...theme.applyStyles('dark', {
        color: theme.palette.grey[600]
      })
    },
    '&.Mui-disabled + .MuiSwitch-track': {
      opacity: 0.7,
      ...(theme.palette.mode === 'dark' && {
        opacity: 0.3
      })
    }
  },
  '& .MuiSwitch-thumb': {
    boxSizing: 'border-box',
    width: 22,
    height: 22
  },
  '& .MuiSwitch-track': {
    borderRadius: 26 / 2,
    backgroundColor: '#E9E9EA',
    opacity: 1,
    transition: theme.transitions.create(['background-color'], {
      duration: 500
    }),
    ...(theme.palette.mode === 'dark' && {
      backgroundColor: '#39393D'
    })
  }
}))

export const StyledCustomCard = styled(Card)(({ theme }) => ({
  position: 'relative',
  backgroundColor: theme.palette.common.white,
  borderRadius: '30px',
  maxWidth: '350px',
  minHeight: '320px',
  width: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  '& .card__headerButton': {
    top: '10px',
    right: '10px',
    position: 'absolute'
  },
  '& .card__actionArea': {
    height: '100%'
  },
  '& .card__content': {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center'
  },
  '& .card__imgBox': {
    width: '100%',
    minHeight: ' 200px',
    display: 'flex',
    justifyContent: 'center'
  },
  '& .card__img': {
    objectFit: 'contain',
    maxWidth: '150px',
    minHeight: '150px'
  },
  '& .card__title': {
    fontSize: '1.35rem',
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: '15px'
  },
  '& .card__description': {
    width: '100%',
    padding: '0 10px',
    textAlign: 'left'
  },
  '& .card__button': {
    fontWeight: 'bold',
    fontSize: '1rem',
    padding: '5px 10px'
  }
}))
