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
  rename: 'common.rename'
}

const BotSettingPage = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { botList, currentBotObjectId, status } = useAppSelector(
    (state) => state.bot
  )
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [botName, setBotName] = useState(currentBot!.chinese_name)
  // 新增Bot Channel相關欄位
  const [channelId, setChannelId] = useState('')
  const [channelSecret, setChannelSecret] = useState('')
  const [channelAccessToken, setChannelAccessToken] = useState('')
  const [loginChannelId, setLoginChannelId] = useState('')
  const [loginChannelSecret, setLoginChannelSecret] = useState('')
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

    await updateBot(updatedBot).unwrap()
    showSuccessToast(t('success.bot_updated'))
    getBots()
  }

  const handleBotDelete = async () => {
    await deleteBot({ bot_uuid: currentBot!.bot_detail_id }).unwrap()
    showSuccessToast(t('success.bot_deleted'))
    navigate(PAGE_PATHS.BOT_LIST)
  }

  return (
    <StyledBotSettingPage disableGutters maxWidth={false}>
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
      {/* 新增Bot Channel設定區域 */}
      <Box className="setting__settingBox">
        <CustomDivider text="Bot Channel 設定" />
        <Box
          className="setting__formBox"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
            background: '#fafbfc',
            borderRadius: 2,
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
            p: 3,
            position: 'relative',
            width: '100%',
            minWidth: 0,
            maxWidth: 'none',
            margin: 0
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <img
              src="/src/assets/line_logo.svg"
              alt="Line"
              style={{ width: 28, height: 28 }}
            />
            <Typography variant="subtitle1" fontWeight={600}>
              Bot Channel
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Channel ID"
              variant="outlined"
              size="small"
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
              sx={{ width: '100%' }}
            />
            <TextField
              label="Channel Secret"
              variant="outlined"
              size="small"
              value={channelSecret}
              onChange={(e) => setChannelSecret(e.target.value)}
              sx={{ width: '100%' }}
            />
          </Box>
          <TextField
            label="Channel Access Token"
            variant="outlined"
            size="small"
            value={channelAccessToken}
            onChange={(e) => setChannelAccessToken(e.target.value)}
            sx={{ width: '100%' }}
          />
          <Box
            sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, mb: 1 }}
          >
            <img
              src="/src/assets/line_logo.svg"
              alt="Line"
              style={{ width: 28, height: 28, opacity: 0.7 }}
            />
            <Typography variant="subtitle1" fontWeight={600}>
              Login Channel
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Login Channel ID"
              variant="outlined"
              size="small"
              value={loginChannelId}
              onChange={(e) => setLoginChannelId(e.target.value)}
              sx={{ width: '100%' }}
            />
            <TextField
              label="Login Channel Secret"
              variant="outlined"
              size="small"
              value={loginChannelSecret}
              onChange={(e) => setLoginChannelSecret(e.target.value)}
              sx={{ width: '100%' }}
            />
          </Box>
          <Button
            variant="contained"
            color="primary"
            sx={{
              mt: 3,
              alignSelf: 'flex-end',
              minWidth: 160,
              fontWeight: 600,
              fontSize: 16
            }}
            onClick={() => {
              // 這裡可以取得所有欄位的值
              // 目前僅console.log，未串API
              console.log({
                channelId,
                channelSecret,
                channelAccessToken,
                loginChannelId,
                loginChannelSecret
              })
            }}
          >
            更新BOT SETTING
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
