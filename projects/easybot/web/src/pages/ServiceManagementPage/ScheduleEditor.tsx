import {
  Box,
  TextField,
  IconButton,
  Checkbox,
  Button,
  MenuItem
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { useTranslation } from 'react-i18next'
import { ServiceScheduleUpdate } from '@/store/apis/reservationApi'

interface ScheduleEditorProps {
  schedules: ServiceScheduleUpdate[]
  onChange: (schedules: ServiceScheduleUpdate[]) => void
}

export const ScheduleEditor = ({
  schedules,
  onChange
}: ScheduleEditorProps) => {
  const { t } = useTranslation()

  const weekdayOptions = [
    { value: 0, label: t('serviceManagementPage.sunday') },
    { value: 1, label: t('serviceManagementPage.monday') },
    { value: 2, label: t('serviceManagementPage.tuesday') },
    { value: 3, label: t('serviceManagementPage.wednesday') },
    { value: 4, label: t('serviceManagementPage.thursday') },
    { value: 5, label: t('serviceManagementPage.friday') },
    { value: 6, label: t('serviceManagementPage.saturday') }
  ]
  const handleChange = <K extends keyof ServiceScheduleUpdate>(
    idx: number,
    field: K,
    value: ServiceScheduleUpdate[K]
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
        <Box
          key={`${sch.reservation_service_schedule_id ?? ''}_${idx}`}
          display="flex"
          gap={1}
          alignItems="center"
          mb={1}
          sx={{
            flexWrap: { xs: 'wrap', md: 'nowrap' },
            minWidth: 0 // Allows flex children to shrink below their content size
          }}
        >
          <TextField
            select
            label={t('serviceManagementPage.scheduleTypeLabel')}
            value={sch.schedule_type ?? 'weekly'}
            onChange={(e) =>
              handleChange(
                idx,
                'schedule_type',
                e.target.value as 'weekly' | 'specific'
              )
            }
            size="small"
            sx={{
              minWidth: 120,
              flex: { xs: '1 1 120px', md: '0 0 120px' }
            }}
          >
            <MenuItem value="weekly">
              {t('serviceManagementPage.weekly')}
            </MenuItem>
            <MenuItem value="specific">
              {t('serviceManagementPage.specific')}
            </MenuItem>
          </TextField>
          {sch.schedule_type === 'weekly' ? (
            <TextField
              select
              label={t('serviceManagementPage.weekday')}
              value={sch.weekday ?? 0}
              onChange={(e) =>
                handleChange(idx, 'weekday', Number(e.target.value))
              }
              size="small"
              sx={{
                minWidth: 130,
                flex: { xs: '1 1 130px', md: '0 0 130px' }
              }}
            >
              {weekdayOptions.map((opt) => (
                <MenuItem key={opt.value} value={opt.value}>
                  {opt.label}
                </MenuItem>
              ))}
            </TextField>
          ) : (
            <TextField
              label={t('serviceManagementPage.dateLabel')}
              type="date"
              value={sch.schedule_date ?? ''}
              onChange={(e) =>
                handleChange(idx, 'schedule_date', e.target.value)
              }
              size="small"
              sx={{
                minWidth: 160,
                flex: { xs: '1 1 160px', md: '0 0 160px' }
              }}
              InputLabelProps={{ shrink: true }}
            />
          )}
          <TextField
            label={t('serviceManagementPage.startTime')}
            type="time"
            value={sch.start_time ?? ''}
            onChange={(e) => handleChange(idx, 'start_time', e.target.value)}
            size="small"
            sx={{
              minWidth: 140,
              flex: { xs: '1 1 140px', md: '0 0 140px' }
            }}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label={t('serviceManagementPage.endTime')}
            type="time"
            value={sch.end_time ?? ''}
            onChange={(e) => handleChange(idx, 'end_time', e.target.value)}
            size="small"
            sx={{
              minWidth: 140,
              flex: { xs: '1 1 140px', md: '0 0 140px' }
            }}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label={t('serviceManagementPage.capacityLabel')}
            type="number"
            value={sch.capacity ?? 1}
            onChange={(e) =>
              handleChange(idx, 'capacity', Number(e.target.value))
            }
            size="small"
            sx={{
              minWidth: 80,
              flex: { xs: '1 1 80px', md: '0 0 80px' }
            }}
          />
          <Box
            display="flex"
            alignItems="center"
            sx={{
              minWidth: 'fit-content',
              flex: { xs: '1 1 auto', md: '0 0 auto' },
              gap: 0.5
            }}
          >
            <Checkbox
              checked={!!sch.is_active}
              onChange={(e) => handleChange(idx, 'is_active', e.target.checked)}
              size="small"
            />
            {t('serviceManagementPage.enable')}
          </Box>
          <IconButton
            onClick={() => handleDelete(idx)}
            size="small"
            sx={{
              minWidth: 'fit-content',
              flex: '0 0 auto'
            }}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ))}
      <Button
        onClick={() => handleAdd('weekly')}
        size="small"
        variant="outlined"
        sx={{ mr: 1 }}
      >
        {t('serviceManagementPage.addWeekly')}
      </Button>
      <Button
        onClick={() => handleAdd('specific')}
        size="small"
        variant="outlined"
      >
        {t('serviceManagementPage.addSpecificDate')}
      </Button>
    </Box>
  )
}
