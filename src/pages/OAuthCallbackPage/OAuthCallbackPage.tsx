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

export const OAuthCallbackPage = () => {
  let isRequest = false
  const navigate = useNavigate()
  const { errorCode } = useAppSelector((state) => state.user)
  const { t } = useTranslation()
  const [oauthLogin] = useOauthLoginUserMutation()
  const [getUser] = useLazyGetUserMeQuery()

  const handleNavigateToLogin = () => {
    navigate(PAGE_PATHS.SIGN_IN)
  }

  const handleOAuthCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const error = urlParams.get('error')
    if (error || !code) {
      setTimeout(() => {
        navigate(PAGE_PATHS.SIGN_IN)
      }, 5000)
      return
    }

    const provider = OAuthProvider.Google
    await oauthLogin({ code, provider })
      .unwrap()
      .then((payload) => {
        localStorage.setItem('token', payload.token)
        getUser().then(() => {
          navigate(PAGE_PATHS.BOT_LIST)
        })
      })
      .catch(() => {
        setTimeout(() => {
          navigate(PAGE_PATHS.SIGN_IN)
        }, 5000)
      })
  }

  useEffect(() => {
    if (!isRequest) {
      handleOAuthCallback()
    }
    isRequest = true
  }, [])

  return (
    <StyledOAuthCallbackPage>
      {!errorCode ? (
        <CustomLoader size="6rem" text={t(oauthCallbackContent.loading)} />
      ) : (
        <Paper elevation={3} className="oauth__paper">
          <ErrorIcon className="oauth__icon" />
          <Typography variant="h4" component="h1" className="oauth__text">
            {t(oauthCallbackContent.failedTitle)}
          </Typography>
          <Typography variant="body1" align="center" className="oauth__text">
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
            className="oauth__button"
            onClick={handleNavigateToLogin}
          >
            {t(oauthCallbackContent.backToLogin)}
          </Button>
        </Paper>
      )}
    </StyledOAuthCallbackPage>
  )
}
