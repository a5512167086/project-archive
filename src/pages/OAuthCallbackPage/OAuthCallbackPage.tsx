import { useEffect } from 'react'
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
import { useAppSelector } from '@/utils/hook'
import { ERROR_CODE_MESSAGE_MAPPING } from '@/configs/common'

const oauthCallbackContent = {
  loading: 'common.loading',
  backToLogin: 'signPage.backToLogin',
  failedTitle: 'error.oauth_failed_title',
  backToLoginHint: 'common.backToLoginHint',
  oauthExistHint: 'error.oauth_exist_hint'
}

type CustomState = {
  provider: OAuthProvider
  action: 'login' | 'bind'
}

const OAuthCallbackPage = () => {
  let isRequest = false
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
    const state = urlParams.get('state')
    if (!state) {
      navigate(PAGE_PATHS.SIGN_IN)
      return
    }

    const { provider, action } = JSON.parse(state) as unknown as CustomState
    const code = urlParams.get('code')
    const error = urlParams.get('error')
    if (error || !code) {
      setTimeout(() => {
        navigate(PAGE_PATHS.SIGN_IN)
      }, 5000)
      return
    }
    if (action === 'login') {
      await oauthLogin({ code, provider: provider as OAuthProvider })
        .unwrap()
        .then((payload) => {
          localStorage.setItem('access_token', payload.access_token)
          localStorage.setItem('refresh_token', payload.refresh_token)
          getUser().then(() => {
            navigate(PAGE_PATHS.BOT_LIST)
          })
        })
        .catch(() => {
          setTimeout(() => {
            navigate(PAGE_PATHS.SIGN_IN)
          }, 5000)
        })
    } else if (action === 'bind') {
      await oauthBind({
        code,
        provider: provider as OAuthProvider,
        action: 'bind'
      })
        .unwrap()
        .finally(() => {
          navigate(PAGE_PATHS.USER_SETTING)
        })
    }
  }

  useEffect(() => {
    if (!isRequest) {
      handleOAuthCallback()
    }
    isRequest = true
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
          <ErrorIcon
            sx={{
              fontSize: '3.5rem',
              marginBottom: '15px'
            }}
          />
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
