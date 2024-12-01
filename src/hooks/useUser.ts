import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { initUser } from '@/store/modules/userSlice'
import { clearUserToken } from '@/utils/helper'
import { useEffect, useState } from 'react'
import { useLazyGetUserMeQuery } from '@/store/apis/userApi'
import { useNavigate } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'
import { initBot } from '@/store/modules/botSlice'

type UseUser = {
  isAuthenticated: boolean
  isAuthFailed: boolean
  logout: () => void
  authStatus: 'idle' | 'loading' | 'succeeded' | 'failed'
}

export const useUser = (): UseUser => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { username, email, status } = useAppSelector((state) => state.user)
  const [getUser] = useLazyGetUserMeQuery()
  const [isAuthFailed, setIsAuthFailed] = useState(false)

  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  const isAuthenticated = Boolean(username && email && token)
  
  const logout = () => {
    if (isAuthenticated) {
      clearUserToken()
      dispatch(initUser())
      dispatch(initBot())
      navigate(PAGE_PATHS.BASE)
    }
  }

  useEffect(() => {
    if (!isAuthenticated && token) {
      getUser()
        .unwrap()
        .catch(() => {
          setIsAuthFailed(true)
          logout()
        })
    }
  }, [])

  return { isAuthenticated, isAuthFailed, logout, authStatus: status }
}
