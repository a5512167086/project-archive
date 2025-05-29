import { CssBaseline, ThemeProvider } from '@mui/material'
import { theme } from '@/configs/theme'
import { RouterProvider } from 'react-router-dom'
import { PAGE_PATHS, router } from '@/routes/index'
import { Provider } from 'react-redux'
import { store } from '@/store/store'
import { SnackbarProvider } from 'notistack'
import { useAppDispatch, useAppSelector } from './utils/hook'
import { useLazyGetUserMeQuery } from './store/apis/userApi'
import { useEffect } from 'react'
import { setAuthenticated } from './store/modules/userSlice'
import { clearUserToken } from './utils/helper'

function AppInitializer() {
  const dispatch = useAppDispatch()
  const [getUser] = useLazyGetUserMeQuery()
  const token =
    localStorage.getItem('access_token') ||
    sessionStorage.getItem('access_token')
  const { isAuthenticated } = useAppSelector((state) => state.user)

  useEffect(() => {
    if (!token) {
      dispatch(setAuthenticated(false))
      return
    }

    if (!isAuthenticated) {
      getUser()
        .unwrap()
        .then(() => {
          dispatch(setAuthenticated(true))
        })
        .catch(() => {
          dispatch(setAuthenticated(false))
          clearUserToken()
          window.location.href = PAGE_PATHS.BASE
        })
    }
  }, [token, isAuthenticated])

  return null
}

function App() {
  return (
    <Provider store={store}>
      <AppInitializer />
      <ThemeProvider theme={theme}>
        <SnackbarProvider maxSnack={3} autoHideDuration={2000}>
          <CssBaseline />
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeProvider>
    </Provider>
  )
}

export default App
