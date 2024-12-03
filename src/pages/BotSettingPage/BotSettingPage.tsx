import { Box, Breadcrumbs, Button, TextField, Typography } from '@mui/material'
import { StyledBotSettingPage } from './BotSettingPage.style'
import { CustomDivider } from '@/components/CustomDivider'
import { CustomDialog } from '@/components/CustomDialog'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'
import { useTranslation } from 'react-i18next'
import {
  useDeleteBotMutation,
  useLazyGetBotsQuery,
  useUpdateBotMutation
} from '@/store/apis/botApi'
import { useAppSelector } from '@/utils/hook'
import { CustomLink } from '@/components/CustomLink'
import { isEmpty } from '@/utils/helper'
import { CustomLoader } from '@/components/CustomLoader'

const botSettingPageContent = {
  botPageTitle: 'botPage.myBot',
  title: 'botSettingPage.title',
  defaultSettingTitle: 'botSettingPage.defaultSettingTitle',
  dangerZoneTitle: 'botSettingPage.dangerZoneTitle',
  deleteBotTitle: 'botSettingPage.deleteBotTitle',
  deleteBotDescription: 'botSettingPage.deleteBotDescription',
  deleteBotConfirmation: 'botSettingPage.deleteBotConfirmation',
  deleteBotButton: 'botSettingPage.deleteBotButton',
  botName: 'botPage.botName',
  rename: 'common.rename'
}

export const BotSettingPage = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { botList, currentBotObjectId, status } = useAppSelector(
    (state) => state.bot
  )
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [botName, setBotName] = useState(currentBot!.bot_name)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [getBots] = useLazyGetBotsQuery()
  const [updateBot] = useUpdateBotMutation()
  const [deleteBot] = useDeleteBotMutation()

  const handleDialogOpen = () => {
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
  }

  const handleRename = async () => {
    try {
      const updatedBot = {
        bot_class_id: currentBot!.class_id,
        bot_name: botName
      }
      await updateBot(updatedBot)
        .unwrap()
        .then(() => {
          getBots()
        })
    } catch (error) {
      console.error('Update failed:', error)
    }
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
      <Breadcrumbs
        sx={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '20px 0' }}
      >
        <CustomLink
          link={PAGE_PATHS.BOT_LIST}
          linkText={t(botSettingPageContent.botPageTitle)}
        />
        <CustomLink
          link={PAGE_PATHS.BOT_LIST + `/${currentBotObjectId}`}
          linkText={currentBot!.bot_name}
          color="text.primary"
          aria-current="page"
        />
        <CustomLink
          link={
            PAGE_PATHS.BOT_LIST +
            `/${currentBotObjectId}` +
            `/${PAGE_PATHS.BOT_SETTING}`
          }
          linkText={t(botSettingPageContent.title)}
          color="text.primary"
          aria-current="page"
        />
      </Breadcrumbs>
      <Typography variant="h5" className="setting__title">
        {t(botSettingPageContent.title)}
      </Typography>
      <Box className="setting__settingBox">
        <CustomDivider text={t(botSettingPageContent.defaultSettingTitle)} />
        <Box className="setting__formBox">
          <TextField
            className="setting__textField"
            required
            margin="dense"
            label={t(botSettingPageContent.botName)}
            type="text"
            variant="outlined"
            size="small"
            value={botName}
            onChange={(e) => setBotName(e.target.value)}
          />
          <Button
            className="setting_formButton"
            variant="outlined"
            color="primary"
            disabled={isEmpty(botName) || status === 'loading'}
            onClick={handleRename}
          >
            {status === 'loading' ? (
              <CustomLoader size={24} />
            ) : (
              t(botSettingPageContent.rename)
            )}
          </Button>
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
