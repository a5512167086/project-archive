import { CssBaseline, ThemeProvider } from '@mui/material'
import { theme } from '@/configs/theme'
import { RouterProvider } from 'react-router-dom'
import { router } from '@/routes/index'
import { Provider } from 'react-redux'
import { store } from '@/store/store'
import { SnackbarProvider } from 'notistack'
function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <SnackbarProvider maxSnack={3} autoHideDuration={3000}>
          <CssBaseline />
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeProvider>
    </Provider>
  )
}

export default App
