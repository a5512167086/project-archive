import { useUser } from '@/hooks/useUser'
import { Outlet } from 'react-router-dom'

const PrivateRoute = () => {
  const { isAuthenticated } = useUser()
  if (isAuthenticated) {
    return <Outlet />
  }
}

export default PrivateRoute
