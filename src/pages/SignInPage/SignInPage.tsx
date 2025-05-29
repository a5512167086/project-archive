import { useState } from 'react'
import {
  Avatar,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Grid2,
  Box,
  Typography,
  Alert
} from '@mui/material'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import { StyledSignInPage } from './SignInPage.style'
import { CustomDivider } from '@/components/CustomDivider'
import { OAuth } from '@/components/OAuth'
import { CustomLink } from '@/components/CustomLink'
import { PAGE_PATHS } from '@/routes'
import { useTranslation } from 'react-i18next'
import {
  useLazyGetUserMeQuery,
  useLoginUserMutation
} from '@/store/apis/userApi'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { clearUserError, setAuthenticated } from '@/store/modules/userSlice'
import { validateEmail } from '@/utils/helper'
import { useNavigate } from 'react-router-dom'
import { ERROR_CODE_MESSAGE_MAPPING } from '@/configs/common'
import { CustomLoader } from '@/components/CustomLoader'

const signInContent = {
  title: 'signPage.signIn',
  or: 'common.or',
  signInButtonText: 'signPage.signIn',
  forgotPassword: 'signPage.forgotPassword',
  notHaveAccount: 'signPage.notHaveAccount',
  email: 'signPage.email',
  password: 'signPage.password',
  rememberMe: 'signPage.rememberMe',
  emailFormatError: 'error.email_format'
}

const SignInPage = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { errorCode } = useAppSelector((state) => state.user)
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(false)
  const [emailError, setEmailError] = useState(false)
  const [loginUser] = useLoginUserMutation()
  const [getUser] = useLazyGetUserMeQuery()

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEmail = e.target.value
    setEmail(newEmail)

    if (emailError && validateEmail(newEmail)) {
      setEmailError(false)
    }
  }

  const handleSignIn = async () => {
    dispatch(clearUserError())
    if (!validateEmail(email)) {
      setEmailError(true)
      return
    }
    setEmailError(false)
    setIsLoading(true)
    await loginUser({ email, password, remember })
      .unwrap()
      .then((payload) => {
        if (remember) {
          localStorage.setItem('access_token', payload.access_token)
          localStorage.setItem('refresh_token', payload.refresh_token)
        } else {
          sessionStorage.setItem('access_token', payload.access_token)
          sessionStorage.setItem('refresh_token', payload.refresh_token)
        }
        getUser()
          .then(() => {
            dispatch(setAuthenticated(true))
            navigate(PAGE_PATHS.BOT_LIST)
          })
          .catch(() => {
            dispatch(setAuthenticated(false))
          })
      })
      .finally(() => {
        setIsLoading(false)
      })
  }

  return (
    <StyledSignInPage maxWidth="xs">
      <Box className="signin__box">
        <Avatar className="signin__avatar">
          <LockOutlinedIcon />
        </Avatar>
        <OAuth />
        <CustomDivider text={t(signInContent.or)} />
        <Typography component="h1" variant="h5">
          {t(signInContent.title)}
        </Typography>
        <Box
          component="form"
          className="signin__formBox"
          onSubmit={(event) => {
            event.preventDefault()
            handleSignIn()
          }}
        >
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            id="email"
            label={t(signInContent.email)}
            name="email"
            autoComplete="email"
            value={email}
            onChange={handleEmailChange}
            error={emailError}
            helperText={emailError && t(signInContent.emailFormatError)}
          />
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            name="password"
            label={t(signInContent.password)}
            type="password"
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {errorCode && (
            <Alert variant="outlined" severity="error">
              {t(
                ERROR_CODE_MESSAGE_MAPPING[
                  errorCode as keyof typeof ERROR_CODE_MESSAGE_MAPPING
                ]
              )}
            </Alert>
          )}
          <FormControlLabel
            control={
              <Checkbox
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                color="primary"
              />
            }
            label={t(signInContent.rememberMe)}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={isLoading || emailError}
            className="sigin__signinButton"
          >
            {isLoading ? (
              <CustomLoader size={25} />
            ) : (
              t(signInContent.signInButtonText)
            )}
          </Button>
          <Grid2 container>
            <Grid2 size={{ xs: 12, sm: 4 }}>
              <CustomLink
                linkText={t(signInContent.forgotPassword)}
                link={PAGE_PATHS.FORGOT_PASSWORD}
                variant="body2"
              />
            </Grid2>
            <Grid2 size={{ xs: 12, sm: 8 }} className="signin__signupButton">
              <CustomLink
                linkText={t(signInContent.notHaveAccount)}
                link={PAGE_PATHS.SIGN_UP}
                variant="body2"
              />
            </Grid2>
          </Grid2>
        </Box>
      </Box>
    </StyledSignInPage>
  )
}

export default SignInPage
