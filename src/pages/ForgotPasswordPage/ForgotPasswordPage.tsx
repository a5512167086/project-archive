import {
  Avatar,
  Button,
  TextField,
  Box,
  Typography,
  Alert
} from '@mui/material'
import HelpCenterIcon from '@mui/icons-material/HelpCenter'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import { StyledForgotPasswordPage } from './ForgotPasswordPage.style'
import { useTranslation } from 'react-i18next'
import { validateEmail } from '@/utils/helper'
import { useState } from 'react'
import { CustomLoader } from '@/components/CustomLoader'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { useForgotPasswordMutation } from '@/store/apis/userApi'
import { clearUserError } from '@/store/modules/userSlice'
import { ERROR_CODE_MESSAGE_MAPPING } from '@/configs/common'
import { useNavigate } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'

const forgotPasswordContent = {
  title: 'signPage.forgotPassword',
  description: 'signPage.forgotPasswordHint',
  email: 'signPage.email',
  emailSendSuccess: 'signPage.sendEmailSuccess',
  buttonText: 'signPage.sendPasswordResetEmail',
  emailFormatError: 'error.email_format',
  backToLogin: 'signPage.backToLogin'
}

const ForgotPasswordPage = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { t } = useTranslation()
  const { errorCode } = useAppSelector((state) => state.user)
  const [forgotPassword] = useForgotPasswordMutation()
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [emailError, setEmailError] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEmail = e.target.value
    setEmail(newEmail)

    if (emailError && validateEmail(newEmail)) {
      setEmailError(false)
    }
  }

  const handleForgotPassword = async () => {
    dispatch(clearUserError())
    if (!validateEmail(email)) {
      setEmailError(true)
      return
    }

    setIsLoading(true)
    await forgotPassword({ email })
      .unwrap()
      .then(() => {
        setIsSuccess(true)
      })
      .finally(() => {
        setIsLoading(false)
      })
  }

  const handleNavigateToLogin = () => {
    navigate(PAGE_PATHS.SIGN_IN)
  }

  return (
    <StyledForgotPasswordPage maxWidth="xs">
      <Box className="forgot__box">
        <Avatar className="forgot__avatar">
          <HelpCenterIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          {t(forgotPasswordContent.title)}
        </Typography>
        <Typography className="forgot__description">
          {t(forgotPasswordContent.description)}
        </Typography>
        <Box
          component="form"
          className="forgot__formBox"
          onSubmit={(event) => {
            event.preventDefault()
            handleForgotPassword()
          }}
        >
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            id="email"
            label={t(forgotPasswordContent.email)}
            name="email"
            autoComplete="email"
            onChange={handleEmailChange}
            value={email}
            error={emailError}
            helperText={emailError && t(forgotPasswordContent.emailFormatError)}
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
          <Button
            type="submit"
            fullWidth
            variant="contained"
            className="forgot__forgotButton"
            disabled={isLoading || isSuccess}
            startIcon={isSuccess && <CheckCircleIcon color="primary" />}
          >
            {isLoading ? (
              <CustomLoader size={25} />
            ) : isSuccess ? (
              t(forgotPasswordContent.emailSendSuccess)
            ) : (
              t(forgotPasswordContent.buttonText)
            )}
          </Button>
          {isSuccess && (
            <Button
              fullWidth
              variant="contained"
              className="forgot__loginButton"
              onClick={handleNavigateToLogin}
            >
              {t(forgotPasswordContent.backToLogin)}
            </Button>
          )}
        </Box>
      </Box>
    </StyledForgotPasswordPage>
  )
}

export default ForgotPasswordPage
