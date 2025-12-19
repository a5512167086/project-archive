import { Box, Button, TextField, Typography } from '@mui/material'
import { StyledBotSettingPage } from './BotSettingPage.style'
import { CustomDivider } from '@/components/CustomDivider'
import { CustomDialog } from '@/components/CustomDialog'
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'
import { useTranslation } from 'react-i18next'
import {
  useDeleteBotMutation,
  useLazyGetBotsQuery,
  useUpdateBotMutation,
  UpdateBotRequest
} from '@/store/apis/botApi'
import { useAppSelector } from '@/utils/hook'
import { isEmpty } from '@/utils/helper'
import { CustomLoader } from '@/components/CustomLoader'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { showSuccessToast } from '@/utils/toast'

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
  update: 'common.update'
}

const BotSettingPage = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { uuid } = useParams()
  const { botList } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.bot_detail_id === uuid)

  const [botName, setBotName] = useState('')
  const [channelId, setChannelId] = useState('')
  const [channelSecret, setChannelSecret] = useState('')
  const [channelAccessToken, setChannelAccessToken] = useState('')
  const [loginChannelId, setLoginChannelId] = useState('')
  const [loginChannelSecret, setLoginChannelSecret] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const [getBots] = useLazyGetBotsQuery()
  const [updateBot, { isLoading: isUpdating }] = useUpdateBotMutation()
  const [deleteBot, { isLoading: isDeleting }] = useDeleteBotMutation()

  useEffect(() => {
    if (currentBot) {
      setBotName(currentBot.chinese_name || '')
      setChannelId(currentBot.channel_id || '')
    }
  }, [currentBot])

  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: botSettingPageContent.botPageTitle
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBot?.bot_detail_id}`,
      linkText: currentBot?.chinese_name || ''
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBot?.bot_detail_id}/${PAGE_PATHS.BOT_SETTING}`,
      linkText: botSettingPageContent.title
    }
  ]

  const handleDialogOpen = () => {
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
  }

  const handleUpdateBot = async () => {
    if (!currentBot) return

    const payload: UpdateBotRequest = {
      bot_uuid: currentBot.bot_detail_id,
      bot_name: botName,
      ...(channelId && { channel_id: channelId }),
      ...(channelSecret && { channel_secret: channelSecret }),
      ...(channelAccessToken && { channel_access_token: channelAccessToken }),
      ...(loginChannelId && { login_channel_id: loginChannelId }),
      ...(loginChannelSecret && { login_channel_secret: loginChannelSecret })
    }

    try {
      await updateBot(payload).unwrap()
      showSuccessToast('success.bot_updated', t)

      setChannelSecret('')
      setChannelAccessToken('')
      setLoginChannelSecret('')

      getBots()
    } catch (error) {
      console.error(error)
    }
  }

  const handleBotDelete = async () => {
    if (!currentBot) return
    try {
      await deleteBot({ bot_uuid: currentBot.bot_detail_id }).unwrap()
      showSuccessToast('success.bot_deleted', t)
      navigate(PAGE_PATHS.BOT_LIST)
    } catch (error) {
      console.error(error)
    }
  }

  if (!currentBot) return <CustomLoader />

  return (
    <StyledBotSettingPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Typography variant="h5" className="setting__title">
        {t(botSettingPageContent.title)}
      </Typography>

      <Box className="setting__settingBox">
        <CustomDivider text={t(botSettingPageContent.defaultSettingTitle)} />
        <Box
          className="setting__formBox"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
            width: '100%',
            mt: 3
          }}
        >
          <TextField
            required
            maxRows={4}
            label={t(botSettingPageContent.botName)}
            type="text"
            variant="outlined"
            size="small"
            value={botName}
            onChange={(e) => setBotName(e.target.value)}
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Channel ID"
              variant="outlined"
              size="small"
              fullWidth
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
            />
            <TextField
              label="Channel Secret"
              variant="outlined"
              size="small"
              fullWidth
              type="password"
              value={channelSecret}
              onChange={(e) => setChannelSecret(e.target.value)}
            />
          </Box>

          <TextField
            label="Channel Access Token"
            variant="outlined"
            size="small"
            fullWidth
            multiline
            maxRows={4}
            value={channelAccessToken}
            onChange={(e) => setChannelAccessToken(e.target.value)}
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Login Channel ID"
              variant="outlined"
              size="small"
              fullWidth
              value={loginChannelId}
              onChange={(e) => setLoginChannelId(e.target.value)}
            />
            <TextField
              label="Login Channel Secret"
              variant="outlined"
              size="small"
              fullWidth
              type="password"
              value={loginChannelSecret}
              onChange={(e) => setLoginChannelSecret(e.target.value)}
            />
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <Button
              className="setting_formButton"
              variant="outlined"
              color="primary"
              disabled={isEmpty(botName) || isUpdating}
              onClick={handleUpdateBot}
            >
              {isUpdating ? (
                <CustomLoader size={24} />
              ) : (
                t(botSettingPageContent.update)
              )}
            </Button>
          </Box>
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
          <Button
            variant="outlined"
            color="error"
            onClick={handleDialogOpen}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <CustomLoader size={24} />
            ) : (
              t(botSettingPageContent.deleteBotButton)
            )}
          </Button>
        </Box>
      </Box>

      <CustomDialog
        open={isDialogOpen}
        handleClose={handleDialogClose}
        title={t(botSettingPageContent.deleteBotConfirmation)}
        dangerButton={true}
        onSubmit={handleBotDelete}
      />
    </StyledBotSettingPage>
  )
}

export default BotSettingPage
