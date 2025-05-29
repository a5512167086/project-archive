import { useAppDispatch } from '@/utils/hook'
import { setAuthenticated } from '@/store/modules/userSlice'
import { initUser } from '@/store/modules/userSlice'
import { clearUserToken } from '@/utils/helper'
import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'
import { initBot } from '@/store/modules/botSlice'

type UseUser = {
  isAuthFailed: boolean
  setIsAuthFailed: (data: boolean) => void
  logout: () => void
}

export const useUser = (): UseUser => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const [isAuthFailed, setIsAuthFailed] = useState(false)

  const logout = useCallback(() => {
    console.log('logout')
    clearUserToken()
    dispatch(initUser())
    dispatch(initBot())
    dispatch(setAuthenticated(false))
    setIsAuthFailed(false)
    navigate(PAGE_PATHS.BASE)
  }, [dispatch, navigate])

  return {
    isAuthFailed,
    setIsAuthFailed,
    logout
  }
}
