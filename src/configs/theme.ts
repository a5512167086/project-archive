import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    primary: {
      main: '#333333',
      light: '#4F4F4F',
      dark: '#1A1A1A'
    },
    secondary: {
      main: '#B3B3B3',
      light: '#E0E0E0',
      dark: '#8C8C8C'
    },
    background: {
      default: '#F5F5F5',
      paper: '#FFFFFF'
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
      disabled: '#BDBDBD'
    },
    divider: '#E0E0E0'
  }
})
