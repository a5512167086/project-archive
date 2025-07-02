import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { StyledReservationManagementPage } from './ReservationManagementPage.style'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import {
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
  Grid
} from '@mui/material'
import { PAGE_PATHS } from '@/routes'
import { useAppSelector } from '@/utils/hook'
import { useTranslation } from 'react-i18next'
import { theme } from '@/configs/theme'
import { useEffect, useMemo, useState } from 'react'
import {
  useLazyGetReservationsQuery,
  ReservationData,
  useUpdateReservationMutation,
  UpdateReservationRequest
} from '@/store/apis/reservationApi'
import { useApiErrorHandler } from '@/hooks/useApiErrorHandler'

const reservationManagementPageContent = {
  title: 'reservationManagementPage.title',
  botPageTitle: 'botPage.myBot'
}

const ReservationManagementPage = () => {
  const { t } = useTranslation()
  const { handleError, showSuccess } = useApiErrorHandler()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

  // API hooks
  const [getReservations, { data: reservations = [] }] =
    useLazyGetReservationsQuery()
  const [updateReservation] = useUpdateReservationMutation()

  // Dialog state
  const [selectedReservation, setSelectedReservation] =
    useState<ReservationData | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editForm, setEditForm] = useState<Partial<UpdateReservationRequest>>(
    {}
  )

  // Fetch reservations when component mounts or bot changes
  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getReservations({ bot_uuid: currentBot.bot_detail_id })
    }
  }, [currentBot, getReservations])

  // Handle reservation click
  const handleReservationClick = (reservation: ReservationData) => {
    setSelectedReservation(reservation)
    setEditForm({
      bot_uuid: currentBot!.bot_detail_id,
      reservation_id: reservation.reservation_id,
      reservation_date: reservation.reservation_date,
      start_time: reservation.start_time,
      payment_method: reservation.payment_method as
        | 'cash'
        | 'bank_transfer'
        | 'credit_card',
      payment_status: reservation.payment_status as
        | 'paid'
        | 'unpaid'
        | 'refunded',
      status: reservation.status,
      note: reservation.notes || ''
    })
    setDialogOpen(true)
  }

  // Handle form change
  const handleFormChange = (
    field: keyof UpdateReservationRequest,
    value: string
  ) => {
    setEditForm((prev) => ({ ...prev, [field]: value }))
  }

  // Handle form submit
  const handleSubmit = async () => {
    if (!editForm.bot_uuid || !editForm.reservation_id) return

    try {
      await updateReservation(editForm as UpdateReservationRequest).unwrap()
      showSuccess('success.data_updated')
      setDialogOpen(false)
      // Refresh reservations
      if (currentBot?.bot_detail_id) {
        getReservations({ bot_uuid: currentBot.bot_detail_id })
      }
    } catch (error) {
      handleError(error)
    }
  }

  // Handle dialog close
  const handleDialogClose = () => {
    setDialogOpen(false)
    setSelectedReservation(null)
    setEditForm({})
  }

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
            // Handle event click - show modal with reservation details
            const reservation = info.event.extendedProps.reservation
            handleReservationClick(reservation)
          }}
          loading={(loading) => {
            // Handle loading state
            console.log('Calendar loading:', loading)
          }}
        />
      </Box>

      {/* Reservation Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleDialogClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {t('reservationManagementPage.reservationDetails')}
        </DialogTitle>
        <DialogContent>
          {selectedReservation && (
            <Box sx={{ pt: 2 }}>
              {/* Basic Information */}
              <Typography variant="h6" gutterBottom>
                {t('reservationManagementPage.basicInfo')}
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    {t('reservationManagementPage.serviceName')}
                  </Typography>
                  <Typography variant="body1">
                    {selectedReservation.service_name}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    {t('common.price')}
                  </Typography>
                  <Typography variant="body1">
                    ${selectedReservation.price}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label={t('reservationManagementPage.reservationDate')}
                    type="date"
                    value={editForm.reservation_date || ''}
                    onChange={(e) =>
                      handleFormChange('reservation_date', e.target.value)
                    }
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label={t('reservationManagementPage.startTime')}
                    type="time"
                    value={editForm.start_time || ''}
                    onChange={(e) =>
                      handleFormChange('start_time', e.target.value)
                    }
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              {/* Status and Payment */}
              <Typography variant="h6" gutterBottom>
                {t('reservationManagementPage.statusAndPayment')}
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth>
                    <InputLabel>
                      {t('reservationManagementPage.status')}
                    </InputLabel>
                    <Select
                      value={editForm.status || ''}
                      label={t('reservationManagementPage.status')}
                      onChange={(e) =>
                        handleFormChange('status', e.target.value)
                      }
                    >
                      <MenuItem value="pending">
                        {t('reservationManagementPage.pending')}
                      </MenuItem>
                      <MenuItem value="confirmed">
                        {t('reservationManagementPage.confirmed')}
                      </MenuItem>
                      <MenuItem value="cancelled">
                        {t('reservationManagementPage.cancelled')}
                      </MenuItem>
                      <MenuItem value="completed">
                        {t('reservationManagementPage.completed')}
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth>
                    <InputLabel>
                      {t('reservationManagementPage.paymentMethod')}
                    </InputLabel>
                    <Select
                      value={editForm.payment_method || ''}
                      label={t('reservationManagementPage.paymentMethod')}
                      onChange={(e) =>
                        handleFormChange('payment_method', e.target.value)
                      }
                    >
                      <MenuItem value="cash">
                        {t('reservationManagementPage.cash')}
                      </MenuItem>
                      <MenuItem value="bank_transfer">
                        {t('reservationManagementPage.bankTransfer')}
                      </MenuItem>
                      <MenuItem value="credit_card">
                        {t('reservationManagementPage.creditCard')}
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth>
                    <InputLabel>
                      {t('reservationManagementPage.paymentStatus')}
                    </InputLabel>
                    <Select
                      value={editForm.payment_status || ''}
                      label={t('reservationManagementPage.paymentStatus')}
                      onChange={(e) =>
                        handleFormChange('payment_status', e.target.value)
                      }
                    >
                      <MenuItem value="paid">
                        {t('reservationManagementPage.paid')}
                      </MenuItem>
                      <MenuItem value="unpaid">
                        {t('reservationManagementPage.unpaid')}
                      </MenuItem>
                      <MenuItem value="refunded">
                        {t('reservationManagementPage.refunded')}
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              {/* Selected Options */}
              <Typography variant="h6" gutterBottom>
                {t('reservationManagementPage.selectedOptions')}
              </Typography>
              <Box sx={{ mb: 3 }}>
                {selectedReservation.selected_option_groups.map(
                  (group, index) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Typography
                        variant="subtitle1"
                        sx={{ fontWeight: 'bold', mb: 1 }}
                      >
                        {group.group_name}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {group.selected_options.map((option, optionIndex) => (
                          <Chip
                            key={optionIndex}
                            label={option.option_name}
                            variant="outlined"
                            size="small"
                          />
                        ))}
                      </Box>
                    </Box>
                  )
                )}
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Notes */}
              <Typography variant="h6" gutterBottom>
                {t('reservationManagementPage.notes')}
              </Typography>
              <TextField
                multiline
                rows={3}
                value={editForm.note || ''}
                onChange={(e) => handleFormChange('note', e.target.value)}
                placeholder={t('reservationManagementPage.notesPlaceholder')}
                fullWidth
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>{t('common.cancel')}</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </StyledReservationManagementPage>
  )
}

export default ReservationManagementPage
