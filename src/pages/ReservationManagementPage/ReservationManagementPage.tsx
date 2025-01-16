import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { StyledReservationManagementPage } from './ReservationManagementPage.style'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { Box, Typography } from '@mui/material'
import { PAGE_PATHS } from '@/routes'
import { useAppSelector } from '@/utils/hook'
import { useTranslation } from 'react-i18next'
import { theme } from '@/configs/theme'

const reservationManagementPageContent = {
  title: 'reservationManagementPage.title',
  botPageTitle: 'botPage.myBot'
}

const ReservationManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: reservationManagementPageContent.botPageTitle
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBotObjectId}`,
      linkText: currentBot!.bot_name
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}/${PAGE_PATHS.KNOWLEDGE_MOUDLE}`,
      linkText: reservationManagementPageContent.title
    }
  ]
  return (
    <StyledReservationManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box className="knowledge__titleBox">
        <Typography variant="h5" className="knowledge__title">
          {t(reservationManagementPageContent.title)}
        </Typography>
        <FullCalendar
          aspectRatio={3}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView={'dayGridMonth'}
          headerToolbar={{
            left: 'prev,next',
            center: 'title',
            right: 'dayGridMonth,dayGridWeek,dayGridDay'
          }}
          eventColor={theme.palette.primary.main}
          eventBorderColor={theme.palette.secondary.main}
          editable
          events={[
            { title: 'Event 1', date: '2025-01-20', end: '2025-01-22' },
            { title: 'Event 2', date: '2025-01-21' }
          ]}
        />
      </Box>
    </StyledReservationManagementPage>
  )
}

export default ReservationManagementPage
