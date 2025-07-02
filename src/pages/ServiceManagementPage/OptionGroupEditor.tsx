import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Button,
  TextField,
  Typography,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  DragIndicator as DragIcon
} from '@mui/icons-material'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy
} from '@dnd-kit/sortable'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

export interface OptionGroupData {
  group_name: string
  group_description?: string
  selection_type: 'single' | 'multiple'
  is_required: boolean
  display_order: number
  is_active: boolean
  options: OptionData[]
}

export interface OptionData {
  option_name: string
  option_description?: string
  price: number
  display_order: number
  is_active: boolean
}

interface OptionGroupEditorProps {
  optionGroups: OptionGroupData[]
  onChange: (optionGroups: OptionGroupData[]) => void
}

// 可拖拽的選項群組組件
const SortableOptionGroup: React.FC<{
  group: OptionGroupData
  groupIndex: number
  isExpanded: boolean
  t: (key: string, options?: { [key: string]: string | number }) => string
  onToggleExpand: () => void
  onGroupChange: (
    field: keyof OptionGroupData,
    value: string | boolean | number
  ) => void
  onDeleteGroup: () => void
  onAddOption: () => void
  onDeleteOption: (optionIndex: number) => void
  onOptionChange: (
    optionIndex: number,
    field: keyof OptionData,
    value: string | number | boolean
  ) => void
}> = ({
  group,
  groupIndex,
  isExpanded,
  t,
  onToggleExpand,
  onGroupChange,
  onDeleteGroup,
  onAddOption,
  onDeleteOption,
  onOptionChange
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: `group-${groupIndex}` })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1
  }

  return (
    <Paper
      ref={setNodeRef}
      style={style}
      sx={{
        mb: 2,
        cursor: isDragging ? 'grabbing' : 'default'
      }}
    >
      {/* 拖拽區域 */}
      <Box
        display="flex"
        alignItems="center"
        p={1}
        sx={{
          borderBottom: '1px solid',
          borderColor: 'divider',
          backgroundColor: 'grey.50'
        }}
      >
        <Box
          {...attributes}
          {...listeners}
          display="flex"
          alignItems="center"
          mr={1}
          sx={{
            cursor: 'grab',
            opacity: 0.7,
            '&:hover': {
              opacity: 1
            },
            '&:active': {
              cursor: 'grabbing'
            }
          }}
        >
          <DragIcon fontSize="small" color="action" />
        </Box>
        <Typography sx={{ flexGrow: 1, fontWeight: 500 }}>
          {group.group_name ||
            t('serviceManagementPage.groupNumber', { number: groupIndex + 1 })}
        </Typography>
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation()
            onDeleteGroup()
          }}
        >
          <DeleteIcon />
        </IconButton>
      </Box>

      <Accordion expanded={isExpanded} onChange={onToggleExpand}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '&:hover': {
              backgroundColor: 'action.hover'
            }
          }}
        >
          <Typography>
            {t('serviceManagementPage.editGroupSettings')}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            <TextField
              label={t('serviceManagementPage.groupName')}
              value={group.group_name}
              onChange={(e) => onGroupChange('group_name', e.target.value)}
              required
              fullWidth
            />
            <TextField
              label={t('serviceManagementPage.groupDescription')}
              value={group.group_description || ''}
              onChange={(e) =>
                onGroupChange('group_description', e.target.value)
              }
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>
                {t('serviceManagementPage.selectionType')}
              </InputLabel>
              <Select
                value={group.selection_type}
                label={t('serviceManagementPage.selectionType')}
                onChange={(e) =>
                  onGroupChange(
                    'selection_type',
                    e.target.value as 'single' | 'multiple'
                  )
                }
              >
                <MenuItem value="single">
                  {t('serviceManagementPage.singleSelection')}
                </MenuItem>
                <MenuItem value="multiple">
                  {t('serviceManagementPage.multipleSelection')}
                </MenuItem>
              </Select>
            </FormControl>

            {/* Group Settings Row */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    checked={group.is_required}
                    onChange={(e) =>
                      onGroupChange('is_required', e.target.checked)
                    }
                  />
                }
                label={t('serviceManagementPage.isRequired')}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={group.is_active}
                    onChange={(e) =>
                      onGroupChange('is_active', e.target.checked)
                    }
                  />
                }
                label={
                  group.is_active ? t('common.active') : t('common.inactive')
                }
              />
            </Box>

            {/* 選項編輯 */}
            <Box>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                mb={1}
              >
                <Typography variant="subtitle1">
                  {t('serviceManagementPage.options')}
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={onAddOption}
                >
                  {t('serviceManagementPage.addOption')}
                </Button>
              </Box>

              {group.options.map((option, optionIndex) => (
                <SortableOption
                  key={`option-${groupIndex}-${optionIndex}`}
                  option={option}
                  optionIndex={optionIndex}
                  groupIndex={groupIndex}
                  t={t}
                  onOptionChange={onOptionChange}
                  onDeleteOption={onDeleteOption}
                />
              ))}
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>
    </Paper>
  )
}

// 可拖拽的選項組件
const SortableOption: React.FC<{
  option: OptionData
  optionIndex: number
  groupIndex: number
  t: (key: string, options?: { [key: string]: string | number }) => string
  onOptionChange: (
    optionIndex: number,
    field: keyof OptionData,
    value: string | number | boolean
  ) => void
  onDeleteOption: (optionIndex: number) => void
}> = ({
  option,
  optionIndex,
  groupIndex,
  t,
  onOptionChange,
  onDeleteOption
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: `option-${groupIndex}-${optionIndex}` })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1
  }

  return (
    <Paper
      ref={setNodeRef}
      style={style}
      sx={{
        p: 2,
        mb: 1,
        bgcolor: 'grey.50',
        cursor: isDragging ? 'grabbing' : 'grab',
        '&:hover': {
          bgcolor: 'grey.100'
        }
      }}
    >
      <Box display="flex" alignItems="center" gap={2}>
        <Box
          {...attributes}
          {...listeners}
          display="flex"
          alignItems="center"
          sx={{
            cursor: 'grab',
            opacity: 0.7,
            '&:hover': {
              opacity: 1
            },
            '&:active': {
              cursor: 'grabbing'
            }
          }}
        >
          <DragIcon fontSize="small" color="action" />
        </Box>
        <TextField
          label={t('serviceManagementPage.optionName')}
          value={option.option_name}
          onChange={(e) =>
            onOptionChange(optionIndex, 'option_name', e.target.value)
          }
          size="small"
          required
        />
        <TextField
          label={t('serviceManagementPage.optionDescription')}
          value={option.option_description || ''}
          onChange={(e) =>
            onOptionChange(optionIndex, 'option_description', e.target.value)
          }
          size="small"
        />
        <TextField
          label={t('serviceManagementPage.additionalPrice')}
          type="number"
          value={option.price}
          onChange={(e) =>
            onOptionChange(optionIndex, 'price', Number(e.target.value))
          }
          size="small"
          sx={{ width: 120 }}
        />
        <FormControlLabel
          control={
            <Switch
              checked={option.is_active}
              onChange={(e) =>
                onOptionChange(optionIndex, 'is_active', e.target.checked)
              }
              size="small"
            />
          }
          label={option.is_active ? t('common.active') : t('common.inactive')}
          sx={{ minWidth: 100 }}
        />
        <IconButton size="small" onClick={() => onDeleteOption(optionIndex)}>
          <DeleteIcon />
        </IconButton>
      </Box>
    </Paper>
  )
}

export const OptionGroupEditor: React.FC<OptionGroupEditorProps> = ({
  optionGroups,
  onChange
}) => {
  const { t } = useTranslation()
  const [expandedGroup, setExpandedGroup] = useState<number | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates
    })
  )

  const handleAddGroup = () => {
    const newGroup: OptionGroupData = {
      group_name: '',
      group_description: '',
      selection_type: 'single',
      is_required: false,
      display_order: optionGroups.length,
      is_active: true,
      options: []
    }
    onChange([...optionGroups, newGroup])
    setExpandedGroup(optionGroups.length)
  }

  const handleDeleteGroup = (index: number) => {
    const newGroups = optionGroups.filter((_, i) => i !== index)
    // 重新排序 display_order
    const reorderedGroups = newGroups.map((group, i) => ({
      ...group,
      display_order: i
    }))
    onChange(reorderedGroups)
  }

  const handleGroupChange = (
    index: number,
    field: keyof OptionGroupData,
    value: string | boolean | number
  ) => {
    const newGroups = [...optionGroups]
    newGroups[index] = { ...newGroups[index], [field]: value }
    onChange(newGroups)
  }

  const handleDragEndGroup = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = optionGroups.findIndex(
        (_, i) => `group-${i}` === active.id
      )
      const newIndex = optionGroups.findIndex(
        (_, i) => `group-${i}` === over.id
      )

      const newGroups = arrayMove(optionGroups, oldIndex, newIndex).map(
        (group, i) => ({
          ...group,
          display_order: i
        })
      )

      onChange(newGroups)
    }
  }

  const handleDragEndOption = (groupIndex: number) => (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const activeId = active.id as string
      const overId = over.id as string

      const oldIndex = parseInt(activeId.split('-')[2])
      const newIndex = parseInt(overId.split('-')[2])

      const newGroups = [...optionGroups]
      newGroups[groupIndex].options = arrayMove(
        newGroups[groupIndex].options,
        oldIndex,
        newIndex
      ).map((option, i) => ({
        ...option,
        display_order: i
      }))

      onChange(newGroups)
    }
  }

  const handleAddOption = (groupIndex: number) => {
    const newOption: OptionData = {
      option_name: '',
      option_description: '',
      price: 0,
      display_order: optionGroups[groupIndex].options.length,
      is_active: true
    }

    const newGroups = [...optionGroups]
    newGroups[groupIndex].options = [
      ...newGroups[groupIndex].options,
      newOption
    ]
    onChange(newGroups)
  }

  const handleDeleteOption = (groupIndex: number, optionIndex: number) => {
    const newGroups = [...optionGroups]
    newGroups[groupIndex].options = newGroups[groupIndex].options.filter(
      (_, i) => i !== optionIndex
    )
    // 重新排序選項的 display_order
    newGroups[groupIndex].options = newGroups[groupIndex].options.map(
      (option, i) => ({
        ...option,
        display_order: i
      })
    )
    onChange(newGroups)
  }

  const handleOptionChange = (
    groupIndex: number,
    optionIndex: number,
    field: keyof OptionData,
    value: string | number | boolean
  ) => {
    const newGroups = [...optionGroups]
    newGroups[groupIndex].options[optionIndex] = {
      ...newGroups[groupIndex].options[optionIndex],
      [field]: value
    }
    onChange(newGroups)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    // 判断是群组拖拽还是选项拖拽
    if (activeId.startsWith('group-') && overId.startsWith('group-')) {
      // 群组拖拽
      handleDragEndGroup(event)
    } else if (activeId.startsWith('option-') && overId.startsWith('option-')) {
      // 选项拖拽 - 需要找到对应的群组
      const activeGroupIndex = parseInt(activeId.split('-')[1])
      handleDragEndOption(activeGroupIndex)(event)
    }
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
          {t('serviceManagementPage.optionGroup')}
        </Typography>
        <Button
          startIcon={<AddIcon />}
          onClick={handleAddGroup}
          variant="outlined"
        >
          {t('serviceManagementPage.addOptionGroup')}
        </Button>
      </Box>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={[
            ...optionGroups.map((_, index) => `group-${index}`),
            ...optionGroups.flatMap((group, groupIndex) =>
              group.options.map(
                (_, optionIndex) => `option-${groupIndex}-${optionIndex}`
              )
            )
          ]}
          strategy={verticalListSortingStrategy}
        >
          {optionGroups.map((group, groupIndex) => (
            <SortableOptionGroup
              key={groupIndex}
              group={group}
              groupIndex={groupIndex}
              t={t}
              isExpanded={expandedGroup === groupIndex}
              onToggleExpand={() =>
                setExpandedGroup(
                  expandedGroup === groupIndex ? null : groupIndex
                )
              }
              onGroupChange={(field, value) =>
                handleGroupChange(groupIndex, field, value)
              }
              onDeleteGroup={() => handleDeleteGroup(groupIndex)}
              onAddOption={() => handleAddOption(groupIndex)}
              onDeleteOption={(optionIndex) =>
                handleDeleteOption(groupIndex, optionIndex)
              }
              onOptionChange={(optionIndex, field, value) =>
                handleOptionChange(groupIndex, optionIndex, field, value)
              }
            />
          ))}
        </SortableContext>
      </DndContext>
    </Box>
  )
}
