import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import { StyledOAuth } from './OAuth.style'
import { useTranslation } from 'react-i18next'
import LineIcon from '@/assets/line_logo.svg?react'
import { useState } from 'react'

const oauthContent = {
  google: 'signPage.google',
  line: 'signPage.line',
  line_dialog_title: 'signPage.line_dialog_title',
  line_dialog_content: 'signPage.line_dialog_content',
  close: 'common.close',
  agree: 'signPage.signIn'
}

export const OAuth = () => {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)

  const handleClickOpen = () => {
    setOpen(true)
  }

  const handleClose = () => {
    setOpen(false)
  }

  const handleGoogleLogin = () => {
    const client_id =
      '48844684655-se9surcs5rvd5ek14o1b39k0lbhvk6on.apps.googleusercontent.com'
    const redirect_uri = `${location.origin}/oauth-callback?login_type=google`
    const scope =
      'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid'
    const response_type = 'code'
    const access_type = 'offline'
    const oauthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${client_id}&redirect_uri=${redirect_uri}&response_type=${response_type}&scope=${scope}&access_type=${access_type}`

    window.location.href = oauthUrl
  }

  const handleLineLogin = () => {
    const client_id = '2006727725'
    const redirect_uri = `${location.origin}/oauth-callback?login_type=line`
    const state = Math.random().toString(36).substring(2, 15)
    const scope = 'profile%20openid%20email	'
    const response_type = 'code'
    const oauthUrl = `https://access.line.me/oauth2/v2.1/authorize?response_type=${response_type}&client_id=${client_id}&redirect_uri=${encodeURIComponent(
      redirect_uri
    )}&state=${state}&scope=${scope}`

    window.location.href = oauthUrl
  }

  return (
    <StyledOAuth maxWidth="xs">
      <Button
        onClick={handleGoogleLogin}
        fullWidth
        variant="contained"
        className="oauth__button"
        startIcon={<GoogleIcon />}
      >
        {t(oauthContent.google)}
      </Button>

      <Button
        onClick={handleClickOpen}
        fullWidth
        variant="contained"
        color="secondary"
        className="oauth__button"
        startIcon={<LineIcon style={{ width: '20px', height: '20px' }} />}
      >
        {t(oauthContent.line)}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">
          {t(oauthContent.line_dialog_title)}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            {t(oauthContent.line_dialog_content)}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>{t(oauthContent.close)}</Button>
          <Button onClick={handleLineLogin} autoFocus>
            {t(oauthContent.agree)}
          </Button>
        </DialogActions>
      </Dialog>
    </StyledOAuth>
  )
}
