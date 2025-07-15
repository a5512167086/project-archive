import { Box, Button, TextField, Typography } from '@mui/material'
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
import { isEmpty } from '@/utils/helper'
import { CustomLoader } from '@/components/CustomLoader'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { useApiHandler } from '@/hooks/useApiHandler'

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

const BotSettingPage = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { handleError, showSuccess } = useApiHandler()
  const { botList, currentBotObjectId, status } = useAppSelector(
    (state) => state.bot
  )
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [botName, setBotName] = useState(currentBot!.chinese_name)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [getBots] = useLazyGetBotsQuery()
  const [updateBot] = useUpdateBotMutation()
  const [deleteBot] = useDeleteBotMutation()
  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: botSettingPageContent.botPageTitle
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBotObjectId}`,
      linkText: currentBot!.chinese_name
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}/${PAGE_PATHS.BOT_SETTING}`,
      linkText: botSettingPageContent.title
    }
  ]

  const handleDialogOpen = () => {
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
  }

  const handleRename = async () => {
    const updatedBot = {
      bot_uuid: currentBot!.bot_detail_id,
      bot_name: botName
    }

    try {
      await updateBot(updatedBot).unwrap()
      showSuccess('success.bot_updated')
      getBots()
    } catch (error) {
      handleError(error)
    }
  }

  const handleBotDelete = async () => {
    try {
      await deleteBot({ bot_uuid: currentBot!.bot_detail_id }).unwrap()
      showSuccess('success.bot_deleted')
      navigate(PAGE_PATHS.BOT_LIST)
    } catch (error) {
      handleError(error)
    }
  }

  return (
    <StyledBotSettingPage>
      <CustomBreadcrumb items={breadcrumbItems} />
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
        open={isDialogOpen}
        handleClose={handleDialogClose}
        title={botSettingPageContent.deleteBotConfirmation}
        dangerButton={true}
        onSubmit={handleBotDelete}
      />
    </StyledBotSettingPage>
  )
}

export default BotSettingPage
