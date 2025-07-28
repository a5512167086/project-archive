import { Button } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import { StyledOAuth } from './OAuth.style'
import { useTranslation } from 'react-i18next'
import LineIcon from '@/assets/line_logo.svg?react'
import { useState } from 'react'
import { handleGoogleOAuth, handleLineOAuth } from '@/utils/helper'
import { OAuthActionType } from '@/configs/type'
import { CustomDialog } from '@/components/CustomDialog/CustomDialog'

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

  return (
    <StyledOAuth maxWidth="xs">
      <Button
        onClick={() => {
          handleGoogleOAuth(OAuthActionType.Login)
        }}
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
      <CustomDialog
        open={open}
        handleClose={handleClose}
        title={oauthContent.line_dialog_title}
        description={oauthContent.line_dialog_content}
        fields={[]}
        maxWidth="xs"
        onSubmit={() => {
          handleLineOAuth(OAuthActionType.Login)
        }}
        dangerButton={false}
      />
    </StyledOAuth>
  )
}
