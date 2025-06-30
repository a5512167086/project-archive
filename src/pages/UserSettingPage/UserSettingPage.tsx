import { FormEvent, useEffect, useState } from 'react'
import { Container, Typography, Box, Button, TextField } from '@mui/material'
import Grid from '@mui/material/Grid2'
import { useAppSelector } from '@/utils/hook'
import {
  UserSettingStyledButton,
  UserSettingStyledPaper
} from './UserSettingPage.style'
import { handleGoogleOAuth, handleLineOAuth } from '@/utils/helper'
import { OAuthActionType } from '@/configs/type'
import { useTranslation } from 'react-i18next'
import {
  useChangePasswordMutation,
  useLazyGetOAuthStatusQuery
} from '@/store/apis/userApi'
import { useUser } from '@/hooks/useUser'
import { useApiErrorHandler } from '@/hooks/useApiErrorHandler'

const userSettingPageContent = {
  title: 'userSettingPage.title',
  email: 'userSettingPage.email',
  connectedAccounts: 'userSettingPage.conntectedAccount',
  bindGoogle: 'userSettingPage.bindGoogle',
  bindLine: 'userSettingPage.bindLine',
  changePassword: 'userSettingPage.changePassword',
  currentPassword: 'userSettingPage.currentPassword',
  newPassword: 'userSettingPage.newPassword',
  confirmPassword: 'userSettingPage.confirmPassword',
  changePasswordSuccess: 'userSettingPage.changePasswordSuccess',
  passwordMimatch: 'userSettingPage.passwordMismatch'
}

const UserSettingPage = () => {
  const { t } = useTranslation()
  const { handleError, showSuccess } = useApiErrorHandler()
  const { logout } = useUser()
  const { email, oauthStatus } = useAppSelector((state) => state.user)
  const [changePassword] = useChangePasswordMutation()
  const [getOAuthStatus] = useLazyGetOAuthStatusQuery()
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  useEffect(() => {
    getOAuthStatus()
  }, [])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleInputChange = (e: { target: { name: any; value: any } }) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }))
  }

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault()
    if (formData.newPassword !== formData.confirmPassword) {
      handleError(null, t('error.password_mismatch'))
      setFormData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      })
      return
    }

    try {
      await changePassword({
        old_password: formData.currentPassword,
        new_password: formData.newPassword
      }).unwrap()

      showSuccess('success.password_changed')
      logout()
    } catch (error) {
      handleError(error)
    }
  }

  return (
    <Container maxWidth="md">
      <UserSettingStyledPaper elevation={3}>
        <Typography variant="h4" gutterBottom align="center">
          {t(userSettingPageContent.title)}
        </Typography>
        <Box mb={4}>
          <Typography variant="h6" gutterBottom>
            {t(userSettingPageContent.email)}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {email}
          </Typography>
        </Box>
        <Box mb={4}>
          <Typography variant="h6" gutterBottom>
            {t(userSettingPageContent.connectedAccounts)}
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <UserSettingStyledButton
                variant="outlined"
                color="primary"
                disabled={oauthStatus.google}
                onClick={() => handleGoogleOAuth(OAuthActionType.Bind)}
              >
                {t(userSettingPageContent.bindGoogle)}
              </UserSettingStyledButton>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <UserSettingStyledButton
                variant="outlined"
                color="success"
                disabled={oauthStatus.line}
                onClick={() => handleLineOAuth(OAuthActionType.Bind)}
              >
                {t(userSettingPageContent.bindLine)}
              </UserSettingStyledButton>
            </Grid>
          </Grid>
        </Box>

        <Box component="form" onSubmit={handleChangePassword}>
          <Typography variant="h6" gutterBottom>
            {t(userSettingPageContent.changePassword)}
          </Typography>
          <Grid container spacing={3}>
            <Grid size={12}>
              <TextField
                fullWidth
                type="password"
                label={t(userSettingPageContent.currentPassword)}
                name="currentPassword"
                required
                value={formData.currentPassword}
                onChange={handleInputChange}
                variant="outlined"
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                type="password"
                label={t(userSettingPageContent.newPassword)}
                name="newPassword"
                required
                value={formData.newPassword}
                onChange={handleInputChange}
                variant="outlined"
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                type="password"
                label={t(userSettingPageContent.confirmPassword)}
                name="confirmPassword"
                required
                value={formData.confirmPassword}
                onChange={handleInputChange}
                variant="outlined"
              />
            </Grid>
            <Grid size={12}>
              <Button
                fullWidth
                type="submit"
                variant="contained"
                color="primary"
                size="large"
              >
                {t(userSettingPageContent.changePassword)}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </UserSettingStyledPaper>
    </Container>
  )
}

export default UserSettingPage
