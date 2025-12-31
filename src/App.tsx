import { CssBaseline, ThemeProvider } from '@mui/material'
import { theme } from '@/configs/theme'
import { RouterProvider } from 'react-router-dom'
import { PAGE_PATHS, router } from '@/routes/index'
import { Provider } from 'react-redux'
import { store } from '@/store/store'
import { SnackbarProvider } from 'notistack'
import { useAppDispatch } from './utils/hook'
import { useLazyGetUserMeQuery } from './store/apis/userApi'
import { Suspense, useEffect, useRef } from 'react'
import { setAuthenticated } from './store/modules/userSlice'
import { clearUserToken } from './utils/helper'
import { LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { CustomLoader } from './components/CustomLoader'

function AppInitializer() {
  const dispatch = useAppDispatch()
  const [getUser] = useLazyGetUserMeQuery()
  const initializedRef = useRef(false)

  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    const token =
      localStorage.getItem('access_token') ||
      sessionStorage.getItem('access_token')

    if (!token) {
      dispatch(setAuthenticated(false))
      return
    }

    ;(async () => {
      try {
        console.log('[AppInitializer] token exists, try getUserMe')
        await getUser().unwrap()
        dispatch(setAuthenticated(true))
      } catch (err) {
        console.log('[AppInitializer] getUserMe failed, clear token', err)
        dispatch(setAuthenticated(false))
        clearUserToken()
        window.location.replace(PAGE_PATHS.BASE)
      }
    })()
  }, [dispatch, getUser])

  return null
}

function App() {
  return (
    <Provider store={store}>
      <AppInitializer />
      <Suspense fallback={<CustomLoader />}>
        <ThemeProvider theme={theme}>
          <SnackbarProvider maxSnack={3} autoHideDuration={2000}>
            <CssBaseline />
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <RouterProvider router={router} />
            </LocalizationProvider>
          </SnackbarProvider>
        </ThemeProvider>
      </Suspense>
    </Provider>
  )
}

export default App
