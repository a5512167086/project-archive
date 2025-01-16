import { Avatar, Button, TextField, Box, Typography } from '@mui/material'
import RestartAltIcon from '@mui/icons-material/RestartAlt'
import { useTranslation } from 'react-i18next'
import { StyledResetPasswordPage } from './ResetPasswordPage.style'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { CustomLoader } from '@/components/CustomLoader'
import { isEmpty, isTokenValid } from '@/utils/helper'
import { PAGE_PATHS } from '@/routes'
import { useResetPasswordMutation } from '@/store/apis/userApi'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import { useAppDispatch } from '@/utils/hook'
import { clearUserError } from '@/store/modules/userSlice'

const resetPasswordContent = {
  title: 'signPage.resetPassword',
  description: 'signPage.resetPasswordHint',
  password: 'signPage.newPassword',
  confirmPassword: 'signPage.confirmPassword',
  buttonText: 'signPage.resetPassword',
  passwordMismatchError: 'error.password_mismatch',
  invalidTokenError: 'error.invalid_token',
  passwordResetSuccess: 'signPage.resetPasswordSuccess',
  backToLogin: 'signPage.backToLogin',
  resetSuccess: 'signPage.resetSuccess'
}

const ResetPasswordPage = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { t } = useTranslation()
  const [resetPassword] = useResetPasswordMutation()
  const [searchParams] = useSearchParams()
  const [isInitLoading, setIsInitLoading] = useState(true)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      navigate(PAGE_PATHS.BASE)
      return
    }
    if (isTokenValid(token)) {
      localStorage.removeItem('token')
      sessionStorage.removeItem('token')
      setIsInitLoading(false)
    } else {
      navigate(PAGE_PATHS.BASE)
      return
    }
  }, [])

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPassword = e.target.value
    setPassword(newPassword)
  }

  const handleConfirmPasswordChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const newConfirmPassword = e.target.value
    setConfirmPassword(newConfirmPassword)
    if (passwordError) {
      setPasswordError(false)
    }
  }

  const handleNavigateToLogin = () => {
    navigate(PAGE_PATHS.SIGN_IN)
  }

  const handleResetPassword = async () => {
    dispatch(clearUserError())
    if (password !== confirmPassword) {
      setPasswordError(true)
      return
    }
    setIsLoading(true)
    await resetPassword({ token: token!, new_password: password })
      .unwrap()
      .then(() => {
        setIsSuccess(true)
        if (!isEmpty(token)) {
          searchParams.delete('token')
          navigate(
            {
              pathname: location.pathname,
              search: searchParams.toString()
            },
            { replace: true }
          )
        }
      })
      .catch(() => {
        navigate(PAGE_PATHS.BASE)
      })
      .finally(() => {
        setIsLoading(false)
      })
  }

  if (isInitLoading) {
    return <CustomLoader />
  }

  return (
    <StyledResetPasswordPage maxWidth="xs">
      <Box className="reset__box">
        <Avatar className="reset__avatar">
          <RestartAltIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          {t(resetPasswordContent.title)}
        </Typography>
        <Typography variant="body2" className="reset__description">
          {t(resetPasswordContent.description)}
        </Typography>
        <Box
          component="form"
          className="reset__formBox"
          onSubmit={(event) => {
            event.preventDefault()
            handleResetPassword()
          }}
        >
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            name="password"
            label={t(resetPasswordContent.password)}
            type="password"
            id="password"
            autoComplete="new-password"
            value={password}
            onChange={handlePasswordChange}
          />
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            name="confirmPassword"
            label={t(resetPasswordContent.confirmPassword)}
            type="password"
            id="confirm-password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={handleConfirmPasswordChange}
            error={passwordError}
            helperText={
              passwordError && t(resetPasswordContent.passwordMismatchError)
            }
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            className="reset__resetButton"
            disabled={isLoading || isSuccess}
            startIcon={isSuccess && <CheckCircleIcon color="primary" />}
          >
            {isLoading ? (
              <CustomLoader size={25} />
            ) : isSuccess ? (
              t(resetPasswordContent.resetSuccess)
            ) : (
              t(resetPasswordContent.buttonText)
            )}
          </Button>
          {isSuccess && (
            <Button
              fullWidth
              variant="contained"
              className="forgot__loginButton"
              onClick={handleNavigateToLogin}
            >
              {t(resetPasswordContent.backToLogin)}
            </Button>
          )}
        </Box>
      </Box>
    </StyledResetPasswordPage>
  )
}

export default ResetPasswordPage
