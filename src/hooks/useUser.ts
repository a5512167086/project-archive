import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { initUser } from '@/store/modules/userSlice'
import { clearUserToken } from '@/utils/helper'
import { useEffect, useCallback, useState } from 'react'
import { useLazyGetUserMeQuery } from '@/store/apis/userApi'
import { useNavigate } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'
import { initBot } from '@/store/modules/botSlice'

type UseUser = {
  isAuthenticated: boolean
  isAuthFailed: boolean
  setIsAuthFailed: (value: boolean) => void
  logout: () => void
  authStatus: 'idle' | 'loading' | 'succeeded' | 'failed'
}

export const useUser = (): UseUser => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { username, email, status } = useAppSelector((state) => state.user)
  const [isAuthFailed, setIsAuthFailed] = useState(false)
  const [getUser, { isUninitialized }] = useLazyGetUserMeQuery()

  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  const isAuthenticated = Boolean(username && email && token)

  const logout = useCallback(() => {
    clearUserToken()
    dispatch(initUser())
    dispatch(initBot())
    navigate(PAGE_PATHS.BASE)
  }, [dispatch, navigate])

  useEffect(() => {
    if (token === null) {
      logout()
      return
    }

    if (!isAuthenticated && isUninitialized) {
      getUser()
        .unwrap()
        .catch(() => {
          setIsAuthFailed(true)
          dispatch(initUser())
          dispatch(initBot())
          logout()
        })
    }
  }, [isAuthenticated, token, isUninitialized, getUser, dispatch, logout])

  return {
    isAuthenticated,
    isAuthFailed,
    setIsAuthFailed,
    logout,
    authStatus: status
  }
}
