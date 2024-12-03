import { CustomCard } from '@/components/CustomCard'
import { BotPageModalStyle, StyledBotPage } from './BotPage.style'
import {
  Breadcrumbs,
  Grid2,
  Modal,
  Box,
  Typography,
  Button
} from '@mui/material'
import { ActionType } from '@/components/CustomCard/CustomCard.type'
import SettingsIcon from '@mui/icons-material/Settings'
import AddIcon from '@/assets/add_icon.png'
import BotIcon from '@/assets/bot_icon.png'
import { CustomDialog } from '@/components/CustomDialog'
import { useEffect, useState } from 'react'
import { CustomLink } from '@/components/CustomLink'
import { PAGE_PATHS } from '@/routes'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  BotsResponse,
  useCreateBotMutation,
  useLazyGetBotsQuery
} from '@/store/apis/botApi'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { clearCurrentBot, setCurrentBot } from '@/store/modules/botSlice'
import { CustomLoader } from '@/components/CustomLoader'

const dialogFields = [
  {
    id: 'botName',
    name: 'botName',
    label: 'botPage.botName',
    type: 'text',
    required: true
  },
  {
    id: 'channelId',
    name: 'channelId',
    label: 'botPage.channelId',
    type: 'text',
    required: true
  },
  {
    id: 'channelSecret',
    name: 'channelSecret',
    label: 'botPage.channelSecret',
    type: 'password',
    required: true
  },
  {
    id: 'channelAccessToken',
    name: 'channelAccessToken',
    label: 'botPage.channelAccessToken',
    type: 'password',
    required: true
  }
]

const botPageContent = {
  title: 'botPage.myBot',
  addBot: 'botPage.addBot',
  seeTutorial: 'botPage.seeTutorial',
  setting: 'common.setting',
  modalTitle: 'botPage.webhookUrl',
  modalDescription: 'botPage.webhookHint',
  modalClose: 'common.close'
}

export const BotPage = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { t } = useTranslation()
  const { botList, status } = useAppSelector((state) => state.bot)
  const [getBots] = useLazyGetBotsQuery()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newLineBotWebhookUrl, setNewLineBotWebhookUrl] = useState('')
  const [createBot] = useCreateBotMutation()

  const handleDialogOpen = () => {
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
  }

  const handleModalOpen = (webhookUrl: string) => {
    setIsModalOpen(true)
    setNewLineBotWebhookUrl(webhookUrl)
  }

  const handleModalClose = () => {
    setIsModalOpen(false)
    setNewLineBotWebhookUrl('')
  }

  const handleBotSetting = (bot: BotsResponse) => {
    dispatch(setCurrentBot(bot.object_id))
    navigate(PAGE_PATHS.BOT_LIST + `/${bot.object_id}`)
  }

  const handleCreateBot = async (data: {
    botName: string
    channelId: string
    channelAccessToken: string
    channelSecret: string
  }) => {
    await createBot({
      bot_name: data.botName,
      bot_channel_id: data.channelId,
      bot_channel_access_token: data.channelAccessToken,
      bot_channel_secret: data.channelSecret
    })
      .unwrap()
      .then((data) => {
        handleModalOpen(data.webhook_url)
        getBots()
      })
  }

  useEffect(() => {
    getBots()
    dispatch(clearCurrentBot())
  }, [])

  return status === 'loading' ? (
    <CustomLoader />
  ) : (
    <StyledBotPage maxWidth="lg">
      <Breadcrumbs
        sx={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '20px 0' }}
      >
        <CustomLink
          link={PAGE_PATHS.BOT_LIST}
          linkText={t(botPageContent.title)}
          color="text.primary"
          aria-current="page"
        />
      </Breadcrumbs>
      <Grid2 container spacing={4}>
        <Grid2
          size={{ xs: 12, sm: 6, md: 4 }}
          display="flex"
          justifyContent="center"
        >
          <CustomCard
            imgSrc={AddIcon}
            cardButton={true}
            cardButtonAction={handleDialogOpen}
            titleText={t(botPageContent.addBot)}
            actionType={ActionType.None}
          />
        </Grid2>
        {botList.map((bot) => (
          <Grid2
            size={{ xs: 12, sm: 6, md: 4 }}
            display="flex"
            justifyContent="center"
            key={bot.class_id}
          >
            <CustomCard
              imgSrc={BotIcon}
              cardButton={false}
              titleText={bot.bot_name}
              actionType={ActionType.Button}
              buttonText={t(botPageContent.setting)}
              buttonIcon={<SettingsIcon />}
              buttonAction={() => {
                handleBotSetting(bot)
              }}
            />
          </Grid2>
        ))}
      </Grid2>
      <CustomDialog<{
        botName: string
        channelId: string
        channelAccessToken: string
        channelSecret: string
      }>
        isOpen={isDialogOpen}
        handleClose={handleDialogClose}
        fields={dialogFields}
        title={botPageContent.addBot}
        onSubmit={(data) => handleCreateBot(data)}
        linkText={botPageContent.seeTutorial}
        link={PAGE_PATHS.CREATE_BOT_TURTROIAL}
      />
      <Modal
        open={isModalOpen}
        onClose={(_event, reason) => {
          if (reason === 'backdropClick') return
          handleModalClose()
        }}
        disableEscapeKeyDown
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={BotPageModalStyle.modalBox}>
          <Typography variant="h5" component="h2" id="modal-modal-title">
            {t(botPageContent.modalTitle)}
          </Typography>
          <Typography variant="h6" id="modal-modal-title">
            {t(botPageContent.modalDescription)}
          </Typography>
          <Typography
            id="modal-modal-description"
            sx={BotPageModalStyle.modalDescription}
          >
            {newLineBotWebhookUrl}
          </Typography>
          <Box sx={BotPageModalStyle.modalButton}>
            <Button variant="outlined" onClick={handleModalClose}>
              {t(botPageContent.modalClose)}
            </Button>
          </Box>
        </Box>
      </Modal>
    </StyledBotPage>
  )
}
