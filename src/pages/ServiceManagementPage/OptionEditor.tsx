import { Box, TextField, IconButton, Checkbox, Button, MenuItem } from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { ReservationItemOptionUpdate } from '@/store/apis/reservationApi'

interface OptionEditorProps {
  options: ReservationItemOptionUpdate[]
  onChange: (options: ReservationItemOptionUpdate[]) => void
}

export const OptionEditor = ({ options, onChange }: OptionEditorProps) => {
  const handleChange = <K extends keyof ReservationItemOptionUpdate>(
    idx: number,
    field: K,
    value: ReservationItemOptionUpdate[K]
  ) => {
    const newOptions = [...options]
    newOptions[idx] = { ...newOptions[idx], [field]: value }
    onChange(newOptions)
  }

  const handleAdd = () => {
    onChange([
      ...options,
      { option_name: '', price: 0, type: 'text', is_required: false, is_active: true }
    ])
  }

  const handleDelete = (idx: number) => {
    const newOptions = options.filter((_, i) => i !== idx)
    onChange(newOptions)
  }

  return (
    <Box>
      {options.map((opt, idx) => (
        <Box key={`${opt.option_id ?? ''}_${idx}`} display="flex" gap={1} alignItems="center" mb={1}>
          <TextField
            label="名稱"
            value={opt.option_name ?? ''}
            onChange={e => handleChange(idx, 'option_name', e.target.value)}
            size="small"
          />
          <TextField
            label="描述"
            value={opt.option_description ?? ''}
            onChange={e => handleChange(idx, 'option_description', e.target.value)}
            size="small"
          />
          <TextField
            label="價格"
            type="number"
            value={opt.price ?? 0}
            onChange={e => handleChange(idx, 'price', Number(e.target.value))}
            size="small"
            sx={{ width: 80 }}
          />
          <TextField
            select
            label="類型"
            value={opt.type ?? 'text'}
            onChange={e => handleChange(idx, 'type', e.target.value)}
            size="small"
            sx={{ width: 80 }}
          >
            <MenuItem value="text">文字</MenuItem>
            <MenuItem value="select">選項</MenuItem>
            <MenuItem value="number">數字</MenuItem>
          </TextField>
          <Checkbox
            checked={!!opt.is_required}
            onChange={e => handleChange(idx, 'is_required', e.target.checked)}
          />必填
          <Checkbox
            checked={!!opt.is_active}
            onChange={e => handleChange(idx, 'is_active', e.target.checked)}
          />啟用
          <IconButton onClick={() => handleDelete(idx)}><DeleteIcon /></IconButton>
        </Box>
      ))}
      <Button onClick={handleAdd} size="small" variant="outlined">新增選項</Button>
    </Box>
  )
}