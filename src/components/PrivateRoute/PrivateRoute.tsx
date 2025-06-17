import { PAGE_PATHS } from '@/routes'
import { useAppSelector } from '@/utils/hook'
import { Navigate, Outlet } from 'react-router-dom'

const PrivateRoute = () => {
  const { isAuthenticated } = useAppSelector((state) => state.user)
  if (isAuthenticated === null) {
    return
  }

  if (isAuthenticated) {
    return <Outlet />
  }

  return <Navigate to={PAGE_PATHS.BASE} replace />
}

export default PrivateRoute
