import { useUser } from '@/hooks/useUser'
import { PAGE_PATHS } from '@/routes'
import { Navigate, Outlet } from 'react-router-dom'

const PrivateRoute = () => {
  const { isAuthenticated, authStatus } = useUser()

  if (!isAuthenticated && authStatus == 'failed') {
    return <Navigate to={PAGE_PATHS.BASE} replace />
  }
  return <Outlet />
}

export default PrivateRoute
