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
import { useEffect, useMemo } from 'react'
import { useLazyGetReservationsQuery, ReservationData } from '@/store/apis/reservationApi'

const reservationManagementPageContent = {
  title: 'reservationManagementPage.title',
  botPageTitle: 'botPage.myBot'
}

const ReservationManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  
  // API hook for getting reservations
  const [getReservations, { data: reservations = [] }] = useLazyGetReservationsQuery()

  // Fetch reservations when component mounts or bot changes
  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getReservations({ bot_uuid: currentBot.bot_detail_id })
    }
  }, [currentBot, getReservations])

  // Convert reservation data to FullCalendar events
  const calendarEvents = useMemo(() => {
    return reservations.map((reservation: ReservationData) => {
      // Create event title with service name and status
      const title = `${reservation.service_name} (${reservation.status})`
      
      // Create start and end datetime
      const startDateTime = `${reservation.reservation_date}T${reservation.start_time}`
      const endDateTime = `${reservation.reservation_date}T${reservation.end_time}`
      
      // Determine color based on status
      let backgroundColor = theme.palette.primary.main
      if (reservation.status === 'confirmed') {
        backgroundColor = theme.palette.success.main
      } else if (reservation.status === 'cancelled') {
        backgroundColor = theme.palette.error.main
      } else if (reservation.status === 'pending') {
        backgroundColor = theme.palette.warning.main
      }

      return {
        id: reservation.reservation_id,
        title,
        start: startDateTime,
        end: endDateTime,
        backgroundColor,
        borderColor: backgroundColor,
        extendedProps: {
          reservation,
          price: reservation.price,
          notes: reservation.notes,
          paymentMethod: reservation.payment_method,
          paymentStatus: reservation.payment_status,
          selectedOptions: reservation.selected_option_groups
        }
      }
    })
  }, [reservations])

  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: t(reservationManagementPageContent.botPageTitle)
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBot?.bot_detail_id}`,
      linkText: currentBot?.chinese_name ?? ''
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBot?.bot_detail_id}/${PAGE_PATHS.RESERVATION_MANAGEMENT}`,
      linkText: t(reservationManagementPageContent.title)
    }
  ]

  return (
    <StyledReservationManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box className="reservation__titleBox">
        <Typography variant="h5" className="reservation__title">
          {t(reservationManagementPageContent.title)}
        </Typography>
      </Box>

      <Box className="calendar__wrapper">
        <FullCalendar
          height={'75vh'}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: 'prev,next',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
          }}
          eventColor={theme.palette.primary.main}
          eventBorderColor={theme.palette.secondary.main}
          editable={false}
          events={calendarEvents}
          eventClick={(info) => {
            // Handle event click - you can show a modal with reservation details
            const reservation = info.event.extendedProps.reservation
            console.log('Clicked reservation:', reservation)
            // TODO: Show modal with reservation details
          }}
          loading={(loading) => {
            // Handle loading state
            console.log('Calendar loading:', loading)
          }}
        />
      </Box>
    </StyledReservationManagementPage>
  )
}

export default ReservationManagementPage
