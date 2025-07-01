import React from 'react'
import { useTranslation } from 'react-i18next'
import {
  Box,
  TextField,
  IconButton,
  Button,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Chip
} from '@mui/material'
import { Delete as DeleteIcon, Add as AddIcon } from '@mui/icons-material'

export interface CreateScheduleData {
  weekdays: number[]
  start_time: string
  end_time: string
  capacity?: number
}

interface CreateScheduleEditorProps {
  schedules: CreateScheduleData[]
  onChange: (schedules: CreateScheduleData[]) => void
}

export const CreateScheduleEditor: React.FC<CreateScheduleEditorProps> = ({
  schedules,
  onChange
}) => {
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
  const handleAddSchedule = () => {
    const newSchedule: CreateScheduleData = {
      weekdays: [],
      start_time: '',
      end_time: '',
      capacity: 1
    }
    onChange([...schedules, newSchedule])
  }

  const handleDeleteSchedule = (index: number) => {
    const newSchedules = schedules.filter((_, i) => i !== index)
    onChange(newSchedules)
  }

  const handleScheduleChange = <K extends keyof CreateScheduleData>(
    index: number,
    field: K,
    value: CreateScheduleData[K]
  ) => {
    const newSchedules = [...schedules]
    newSchedules[index] = { ...newSchedules[index], [field]: value }
    onChange(newSchedules)
  }

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h6">
          {t('serviceManagementPage.defaultSchedule')}
        </Typography>
        <Button
          startIcon={<AddIcon />}
          onClick={handleAddSchedule}
          variant="outlined"
        >
          {t('serviceManagementPage.addTimeSlot')}
        </Button>
      </Box>

      {schedules.map((schedule, index) => (
        <Paper key={index} sx={{ p: 2, mb: 2 }}>
          <Box display="flex" flexDirection="column" gap={2}>
            <Box
              display="flex"
              alignItems="center"
              justifyContent="space-between"
            >
              <Typography variant="subtitle2">
                {t('serviceManagementPage.timeSlot')} {index + 1}
              </Typography>
              <IconButton
                size="small"
                onClick={() => handleDeleteSchedule(index)}
              >
                <DeleteIcon />
              </IconButton>
            </Box>

            <FormControl fullWidth>
              <InputLabel>
                {t('serviceManagementPage.selectWeekday')}
              </InputLabel>
              <Select
                multiple
                value={schedule.weekdays}
                onChange={(e) =>
                  handleScheduleChange(
                    index,
                    'weekdays',
                    e.target.value as number[]
                  )
                }
                input={
                  <OutlinedInput
                    label={t('serviceManagementPage.selectWeekday')}
                  />
                }
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => {
                      const option = weekdayOptions.find(
                        (opt) => opt.value === value
                      )
                      return (
                        <Chip key={value} label={option?.label} size="small" />
                      )
                    })}
                  </Box>
                )}
              >
                {weekdayOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box display="flex" gap={2}>
              <TextField
                label={t('serviceManagementPage.startTime')}
                type="time"
                value={schedule.start_time}
                onChange={(e) =>
                  handleScheduleChange(index, 'start_time', e.target.value)
                }
                InputLabelProps={{ shrink: true }}
                fullWidth
              />
              <TextField
                label={t('serviceManagementPage.endTime')}
                type="time"
                value={schedule.end_time}
                onChange={(e) =>
                  handleScheduleChange(index, 'end_time', e.target.value)
                }
                InputLabelProps={{ shrink: true }}
                fullWidth
              />
              <TextField
                label={t('serviceManagementPage.maxCapacity')}
                type="number"
                value={schedule.capacity || 1}
                onChange={(e) =>
                  handleScheduleChange(
                    index,
                    'capacity',
                    Number(e.target.value)
                  )
                }
                inputProps={{ min: 1 }}
                fullWidth
              />
            </Box>
          </Box>
        </Paper>
      ))}
    </Box>
  )
}
