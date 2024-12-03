import { Box, Button, TextField, Typography } from '@mui/material'
import { StyledBotSettingPage } from './BotSettingPage.style'
import { CustomDivider } from '@/components/CustomDivider'
import { CustomDialog } from '@/components/CustomDialog'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'
import { useTranslation } from 'react-i18next'
import { useDeleteBotMutation } from '@/store/apis/botApi'
import { useAppSelector } from '@/utils/hook'

const botSettingPageContent = {
  title: 'botSettingPage.title',
  defaultSettingTitle: 'botSettingPage.defaultSettingTitle',
  dangerZoneTitle: 'botSettingPage.dangerZoneTitle',
  deleteBotTitle: 'botSettingPage.deleteBotTitle',
  deleteBotDescription: 'botSettingPage.deleteBotDescription',
  deleteBotConfirmation: 'botSettingPage.deleteBotConfirmation',
  deleteBotButton: 'botSettingPage.deleteBotButton'
}

export const BotSettingPage = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { currentBot } = useAppSelector((state) => state.bot)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [deleteBot] = useDeleteBotMutation()

  const handleDialogOpen = () => {
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
  }

  const handleBotDelete = () => {
    deleteBot({ bot_class_id: currentBot!.class_id })
      .unwrap()
      .then(() => {
        navigate(PAGE_PATHS.BOT_LIST)
      })
  }

  return (
    <StyledBotSettingPage>
      <Typography variant="h5" className="setting__title">
        {t(botSettingPageContent.title)}
      </Typography>
      <Box className="setting__settingBox">
        <CustomDivider text={t(botSettingPageContent.defaultSettingTitle)} />
        <Box className="setting__formBox">
          <TextField
            required={true}
            margin="dense"
            label="Test"
            type="text"
            fullWidth
            variant="outlined"
          />
        </Box>
      </Box>
      <Box className="setting__settingBox">
        <CustomDivider text={t(botSettingPageContent.dangerZoneTitle)} />
        <Box className="setting__dangerBox">
          <Typography className="setting_deleteText">
            {t(botSettingPageContent.deleteBotTitle)}
            <br />
            {t(botSettingPageContent.deleteBotDescription)}
          </Typography>
          <Button variant="outlined" color="error" onClick={handleDialogOpen}>
            {t(botSettingPageContent.deleteBotButton)}
          </Button>
        </Box>
      </Box>
      <CustomDialog
        isOpen={isDialogOpen}
        handleClose={handleDialogClose}
        title={botSettingPageContent.deleteBotConfirmation}
        dangerButton={true}
        onSubmit={handleBotDelete}
      />
    </StyledBotSettingPage>
  )
}
