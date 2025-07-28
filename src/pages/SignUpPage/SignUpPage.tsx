import { Avatar, Button, TextField, Box, Typography } from '@mui/material'
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt'
import { StyledSignUpPage } from './SignUpPage.style'
import { PAGE_PATHS } from '@/routes'
import { CustomLink } from '@/components/CustomLink'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useState, ChangeEvent } from 'react'
import { validateEmail } from '@/utils/helper'
import { useRegisterUserMutation } from '@/store/apis/userApi'
import { useAppDispatch } from '@/utils/hook'
import { clearUserError } from '@/store/modules/userSlice'
import { CustomLoader } from '@/components/CustomLoader'
import { showSuccessToast } from '@/utils/toast'

const signUpContent = {
  title: 'signPage.signUp',
  signUpButtonText: 'signPage.signUp',
  haveAccount: 'signPage.haveAccount',
  fullName: 'signPage.fullName',
  email: 'signPage.email',
  password: 'signPage.password',
  confirmPassword: 'signPage.confirmPassword',
  emailFormatError: 'error.email_format',
  passwordMismatch: 'error.password_mismatch'
}

const SignUpPage = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { t } = useTranslation()
  const [registerUser] = useRegisterUserMutation()
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [emailError, setEmailError] = useState(false)
  const [passwordError, setPasswordError] = useState(false)

  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newEmail = e.target.value
    setEmail(newEmail)

    if (emailError && validateEmail(newEmail)) {
      setEmailError(false)
    }
  }

  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newPassword = e.target.value
    setPassword(newPassword)
  }

  const handleConfirmPasswordChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newConfirmPassword = e.target.value
    setConfirmPassword(newConfirmPassword)
    if (passwordError) {
      setPasswordError(false)
    }
  }

  const handleSignUp = async () => {
    dispatch(clearUserError())
    if (!validateEmail(email)) {
      setEmailError(true)
      return
    }
    if (password !== confirmPassword) {
      setPasswordError(true)
      return
    }

    setEmailError(false)
    setPasswordError(false)
    setIsLoading(true)

    try {
      await registerUser({ email, username: name, password }).unwrap()
      showSuccessToast(t('success.account_created_success'))
      navigate(PAGE_PATHS.SIGN_IN)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <StyledSignUpPage maxWidth="xs">
      <Box className="signup__box">
        <Avatar className="signup__avatar">
          <PersonAddAltIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          {t(signUpContent.title)}
        </Typography>
        <Box
          component="form"
          className="signup__formBox"
          onSubmit={(event) => {
            event.preventDefault()
            handleSignUp()
          }}
        >
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            id="name"
            label={t(signUpContent.fullName)}
            name="name"
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            id="email"
            label={t(signUpContent.email)}
            name="email"
            autoComplete="email"
            value={email}
            onChange={handleEmailChange}
            error={emailError}
            helperText={emailError && t(signUpContent.emailFormatError)}
          />
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            name="password"
            label={t(signUpContent.password)}
            type="password"
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={handlePasswordChange}
          />
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            name="confirm-password"
            label={t(signUpContent.confirmPassword)}
            type="password"
            id="confirm-password"
            value={confirmPassword}
            onChange={handleConfirmPasswordChange}
            error={passwordError}
            helperText={passwordError && t(signUpContent.passwordMismatch)}
          />
          <Button
            fullWidth
            type="submit"
            variant="contained"
            className="sigin__signupButton"
            disabled={isLoading || emailError || passwordError}
          >
            {isLoading ? (
              <CustomLoader size={25} />
            ) : (
              t(signUpContent.signUpButtonText)
            )}
          </Button>
          <CustomLink
            linkText={t(signUpContent.haveAccount)}
            link={PAGE_PATHS.SIGN_IN}
            variant="body2"
          />
        </Box>
      </Box>
    </StyledSignUpPage>
  )
}

export default SignUpPage
