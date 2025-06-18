import { Box, TextField, IconButton, Checkbox, Button, MenuItem } from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { ReservationItemScheduleUpdate } from '@/store/apis/reservationApi'

interface ScheduleEditorProps {
  schedules: ReservationItemScheduleUpdate[]
  onChange: (schedules: ReservationItemScheduleUpdate[]) => void
}

const weekdayOptions = [
  { value: 0, label: '週日' },
  { value: 1, label: '週一' },
  { value: 2, label: '週二' },
  { value: 3, label: '週三' },
  { value: 4, label: '週四' },
  { value: 5, label: '週五' },
  { value: 6, label: '週六' }
]

export const ScheduleEditor = ({ schedules, onChange }: ScheduleEditorProps) => {
  const handleChange = <K extends keyof ReservationItemScheduleUpdate>(
    idx: number,
    field: K,
    value: ReservationItemScheduleUpdate[K]
  ) => {
    const newSchedules = [...schedules]
    newSchedules[idx] = { ...newSchedules[idx], [field]: value }
    onChange(newSchedules)
  }

  const handleAdd = (type: 'weekly' | 'specific') => {
    onChange([
      ...schedules,
      {
        schedule_type: type,
        weekday: type === 'weekly' ? 1 : undefined,
        schedule_date: type === 'specific' ? '' : undefined,
        start_time: '',
        end_time: '',
        capacity: 1,
        is_closed: false,
        is_active: true
      }
    ])
  }

  const handleDelete = (idx: number) => {
    const newSchedules = schedules.filter((_, i) => i !== idx)
    onChange(newSchedules)
  }

  return (
    <Box>
      {schedules.map((sch, idx) => (
        <Box key={`${sch.reservation_item_schedule_id ?? ''}_${idx}`} display="flex" gap={1} alignItems="center" mb={1}>
          <TextField
            select
            label="類型"
            value={sch.schedule_type ?? 'weekly'}
            onChange={e => handleChange(idx, 'schedule_type', e.target.value as 'weekly' | 'specific')}
            size="small"
            sx={{ width: 80 }}
          >
            <MenuItem value="weekly">每週</MenuItem>
            <MenuItem value="specific">指定日</MenuItem>
          </TextField>
          {sch.schedule_type === 'weekly' ? (
            <TextField
              select
              label="星期"
              value={sch.weekday ?? 0}
              onChange={e => handleChange(idx, 'weekday', Number(e.target.value))}
              size="small"
              sx={{ width: 80 }}
            >
              {weekdayOptions.map(opt => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </TextField>
          ) : (
            <TextField
              label="日期"
              type="date"
              value={sch.schedule_date ?? ''}
              onChange={e => handleChange(idx, 'schedule_date', e.target.value)}
              size="small"
              sx={{ width: 140 }}
              InputLabelProps={{ shrink: true }}
            />
          )}
          <TextField
            label="開始"
            type="time"
            value={sch.start_time ?? ''}
            onChange={e => handleChange(idx, 'start_time', e.target.value)}
            size="small"
            sx={{ width: 110 }}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="結束"
            type="time"
            value={sch.end_time ?? ''}
            onChange={e => handleChange(idx, 'end_time', e.target.value)}
            size="small"
            sx={{ width: 110 }}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="人數"
            type="number"
            value={sch.capacity ?? 1}
            onChange={e => handleChange(idx, 'capacity', Number(e.target.value))}
            size="small"
            sx={{ width: 70 }}
          />
          <Checkbox
            checked={!!sch.is_closed}
            onChange={e => handleChange(idx, 'is_closed', e.target.checked)}
          />關閉
          <Checkbox
            checked={!!sch.is_active}
            onChange={e => handleChange(idx, 'is_active', e.target.checked)}
          />啟用
          <IconButton onClick={() => handleDelete(idx)}><DeleteIcon /></IconButton>
        </Box>
      ))}
      <Button onClick={() => handleAdd('weekly')} size="small" variant="outlined" sx={{ mr: 1 }}>新增每週</Button>
      <Button onClick={() => handleAdd('specific')} size="small" variant="outlined">新增指定日</Button>
    </Box>
  )
}