import { Box, TextField, IconButton, Checkbox, Button } from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { useTranslation } from 'react-i18next'
import { ServiceOptionUpdate } from '@/store/apis/reservationApi'

interface OptionEditorProps {
  options: ServiceOptionUpdate[]
  onChange: (options: ServiceOptionUpdate[]) => void
}

export const OptionEditor = ({ options, onChange }: OptionEditorProps) => {
  const { t } = useTranslation()
  const handleChange = <K extends keyof ServiceOptionUpdate>(
    idx: number,
    field: K,
    value: ServiceOptionUpdate[K]
  ) => {
    const newOptions = [...options]
    newOptions[idx] = { ...newOptions[idx], [field]: value }
    onChange(newOptions)
  }

  const handleAdd = () => {
    onChange([
      ...options,
      {
        option_name: '',
        price: 0,
        display_order: options.length,
        is_active: true
      }
    ])
  }

  const handleDelete = (idx: number) => {
    const newOptions = options.filter((_, i) => i !== idx)
    onChange(newOptions)
  }

  return (
    <Box>
      {options.map((opt, idx) => (
        <Box
          key={`${opt.option_id ?? ''}_${idx}`}
          display="flex"
          gap={1}
          alignItems="center"
          mb={1}
        >
          <TextField
            label={t('serviceManagementPage.optionName')}
            value={opt.option_name ?? ''}
            onChange={(e) => handleChange(idx, 'option_name', e.target.value)}
            size="small"
          />
          <TextField
            label={t('serviceManagementPage.optionDescription')}
            value={opt.option_description ?? ''}
            onChange={(e) =>
              handleChange(idx, 'option_description', e.target.value)
            }
            size="small"
          />
          <TextField
            label={t('common.price')}
            type="number"
            value={opt.price ?? 0}
            onChange={(e) => handleChange(idx, 'price', Number(e.target.value))}
            size="small"
            sx={{ width: 80 }}
          />
          <Checkbox
            checked={!!opt.is_active}
            onChange={(e) => handleChange(idx, 'is_active', e.target.checked)}
          />
          {t('serviceManagementPage.enable')}
          <IconButton onClick={() => handleDelete(idx)}>
            <DeleteIcon />
          </IconButton>
        </Box>
      ))}
      <Button onClick={handleAdd} size="small" variant="outlined">
        {t('serviceManagementPage.addOption')}
      </Button>
    </Box>
  )
}
