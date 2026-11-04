import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { CustomLoader } from '@/components/CustomLoader'
import { useTranslation } from 'react-i18next'
import { PAGE_PATHS } from '@/routes'
import { Button, Paper, Typography } from '@mui/material'
import { StyledOAuthCallbackPage } from './OAuthCallbackPage.style'
import ErrorIcon from '@mui/icons-material/Error'
import {
  OAuthProvider,
  useLazyGetUserMeQuery,
  useOauthBindUserMutation,
  useOauthLoginUserMutation
} from '@/store/apis/userApi'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { ERROR_CODE_MESSAGE_MAPPING } from '@/configs/common'
import { setAuthenticated } from '@/store/modules/userSlice'
import { clearUserToken } from '@/utils/helper'

type CustomState = {
  provider: OAuthProvider
  action: 'login' | 'bind'
}

const oauthCallbackContent = {
  loading: 'common.loading',
  backToLogin: 'signPage.backToLogin',
  failedTitle: 'error.oauth_failed_title',
  backToLoginHint: 'common.backToLoginHint',
  oauthExistHint: 'error.oauth_exist_hint'
}

const OAuthCallbackPage = () => {
  const requestOnceRef = useRef(false)

  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { errorCode, isAuthenticated } = useAppSelector((state) => state.user)
  const { t } = useTranslation()

  const [oauthLogin] = useOauthLoginUserMutation()
  const [oauthBind] = useOauthBindUserMutation()
  const [getUser] = useLazyGetUserMeQuery()

  const handleNavigateToLogin = () => {
    navigate(PAGE_PATHS.SIGN_IN)
  }

  const handleOAuthCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search)
    const stateStr = urlParams.get('state')
    const code = urlParams.get('code')
    const error = urlParams.get('error')

    if (error || !code || !stateStr) {
      setTimeout(() => navigate(PAGE_PATHS.SIGN_IN), 2000)
      return
    }

    let parsed: CustomState
    try {
      parsed = JSON.parse(stateStr) as CustomState
    } catch {
      // 如果你的 state 有做 encodeURIComponent，請改成 JSON.parse(decodeURIComponent(stateStr))
      // parsed = JSON.parse(decodeURIComponent(stateStr)) as CustomState
      setTimeout(() => navigate(PAGE_PATHS.SIGN_IN), 2000)
      return
    }

    const { provider, action } = parsed

    try {
      if (action === 'login') {
        const payload = await oauthLogin({ code, provider }).unwrap()

        // OAuth 登入通常視為 remember：直接存 localStorage
        localStorage.setItem('access_token', payload.access_token)
        localStorage.setItem('refresh_token', payload.refresh_token)

        // 確認 token 已寫入後再打 me
        await getUser().unwrap()

        dispatch(setAuthenticated(true))
        navigate(PAGE_PATHS.BOT_LIST)
        return
      }

      if (action === 'bind') {
        await oauthBind({ code, provider, action: 'bind' }).unwrap()
        navigate(PAGE_PATHS.USER_SETTING)
        return
      }
    } catch {
      // 任何一步失敗：清 token，回登入
      dispatch(setAuthenticated(false))
      clearUserToken()
      setTimeout(() => navigate(PAGE_PATHS.SIGN_IN), 2000)
    }
  }

  useEffect(() => {
    if (requestOnceRef.current) return
    requestOnceRef.current = true
    handleOAuthCallback()
  }, [])

  return (
    <StyledOAuthCallbackPage>
      {!errorCode && (
        <CustomLoader size="6rem" text={t(oauthCallbackContent.loading)} />
      )}

      {errorCode && !isAuthenticated && (
        <Paper
          elevation={3}
          sx={{
            padding: '40px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            backgroundColor: 'background.paper'
          }}
        >
          <ErrorIcon sx={{ fontSize: '3.5rem', marginBottom: '15px' }} />
          <Typography variant="h4" component="h1" sx={{ marginBottom: '15px' }}>
            {t(oauthCallbackContent.failedTitle)}
          </Typography>

          <Typography
            variant="body1"
            align="center"
            sx={{ marginBottom: '15px' }}
          >
            {t(
              ERROR_CODE_MESSAGE_MAPPING[
                errorCode as keyof typeof ERROR_CODE_MESSAGE_MAPPING
              ]
            )}
            {errorCode === 'USER_ALREADY_EXISTS' && (
              <>
                <br /> {t(oauthCallbackContent.oauthExistHint)}
              </>
            )}
            <br />
            {t(oauthCallbackContent.backToLoginHint)}
          </Typography>

          <Button
            fullWidth
            variant="contained"
            onClick={handleNavigateToLogin}
            sx={{ margin: '10px 0' }}
          >
            {t(oauthCallbackContent.backToLogin)}
          </Button>
        </Paper>
      )}
    </StyledOAuthCallbackPage>
  )
}

export default OAuthCallbackPage
