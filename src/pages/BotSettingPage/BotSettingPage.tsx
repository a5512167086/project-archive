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
      link: PAGE_PATHS.BOT_LIST + `/${currentBot?.bot_detail_id}`,
      linkText: currentBot!.chinese_name
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

  const handleRename = async () => {
    const updatedBot = {
      bot_uuid: currentBot!.bot_detail_id,
      bot_name: botName
    }

    await updateBot(updatedBot).unwrap()
    showSuccessToast('success.bot_updated', t)
    getBots()
  }

  const handleBotDelete = async () => {
    await deleteBot({ bot_uuid: currentBot!.bot_detail_id }).unwrap()
    showSuccessToast('success.bot_deleted', t)
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
            gap: 2, // 欄位之間的間距
            width: '100%',
            mt: 2 // 與 Divider 的距離
            // 已移除 background, boxShadow, p, borderRadius 以符合上方風格
          }}
        >
          {/* Bot Channel Section */}
          <Box>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
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
                value={channelSecret}
                onChange={(e) => setChannelSecret(e.target.value)}
              />
            </Box>
            <TextField
              label="Channel Access Token"
              variant="outlined"
              size="small"
              fullWidth
              value={channelAccessToken}
              onChange={(e) => setChannelAccessToken(e.target.value)}
            />
          </Box>

          {/* Login Channel Section */}
          <Box>
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
                value={loginChannelSecret}
                onChange={(e) => setLoginChannelSecret(e.target.value)}
              />
            </Box>
          </Box>

          {/* Action Button */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <Button
              className="setting_formButton" // 使用與上方一致的 class (若 style 有定義)
              variant="outlined" // 或改成 "contained"
              color="primary"
              onClick={() => {
                // TODO: 這裡記得串接 updateBot API
                console.log({
                  channelId,
                  channelSecret,
                  channelAccessToken,
                  loginChannelId,
                  loginChannelSecret
                })
              }}
            >
              更新設定
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
