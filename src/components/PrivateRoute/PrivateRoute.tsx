import { useUser } from '@/hooks/useUser'
import { PAGE_PATHS } from '@/routes'
import { Navigate, Outlet } from 'react-router-dom'

const PrivateRoute = () => {
  const { isAuthenticated } = useUser()

  if (!isAuthenticated) {
    return <Navigate to={PAGE_PATHS.BASE} replace />
  }
  return <Outlet />
}

export default PrivateRoute
