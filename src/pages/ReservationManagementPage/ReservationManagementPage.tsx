import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'

const ReservationManagementPage = () => {
  return (
    <div>
      <FullCalendar aspectRatio={2.5} plugins={[dayGridPlugin]} />
    </div>
  )
}

export default ReservationManagementPage
