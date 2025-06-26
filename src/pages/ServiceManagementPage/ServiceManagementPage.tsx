import { useEffect, useState } from 'react'
import { Box, Button, Typography, TextField } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'
import { PAGE_PATHS } from '@/routes'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { StyledServiceManagementPage } from './ServiceManagementPage.style'
import {
  useLazyGetServicesQuery,
  useInsertServiceMutation,
  useDeleteReservationItemsMutation,
  usePatchReservationItemMutation,
  InsertReservationItemRequest,
  ReservationItemsResponse,
  ReservationItemOptionUpdate,
  ReservationItemScheduleUpdate
} from '@/store/apis/reservationApi'
import { CustomTable } from '@/components/CustomTable'
import { CustomDialog } from '@/components/CustomDialog'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import { OptionEditor } from './OptionEditor'
import { ScheduleEditor } from './ScheduleEditor'

const TEXT = {
  title: 'serviceManagementPage.title',
  botPageTitle: 'botPage.myBot',
  deleteSingleTitle: '刪除服務「{{name}}」？',
  deleteMultiTitle: '刪除選取的服務？',
  deleteButtonText: '刪除已選取'
} as const

const createFields: FieldProps[] = [
  {
    id: 'reservation_name',
    name: 'reservation_name',
    label: '服務名稱',
    type: 'text',
    required: true
  },
  {
    id: 'reservation_description',
    name: 'reservation_description',
    label: '描述',
    type: 'text',
    required: true
  },
  {
    id: 'duration_minutes',
    name: 'duration_minutes',
    label: '時長（分鐘）',
    type: 'number',
    required: true
  },
  {
    id: 'price',
    name: 'price',
    label: '價格',
    type: 'number',
    required: true
  },
  {
    id: 'options',
    name: 'options',
    label: '選項',
    type: 'array',
    required: false,
    fields: [
      {
        id: 'option_name',
        name: 'option_name',
        label: '名稱',
        type: 'text',
        required: true
      },
      {
        id: 'option_description',
        name: 'option_description',
        label: '描述',
        type: 'text',
        required: false
      },
      {
        id: 'price',
        name: 'price',
        label: '價格',
        type: 'number',
        required: true
      },
      {
        id: 'type',
        name: 'type',
        label: '類型',
        type: 'select',
        required: true,
        options: [
          { value: 'text', label: '文字' },
          { value: 'select', label: '選項' },
          { value: 'number', label: '數字' }
        ]
      },
      {
        id: 'is_required',
        name: 'is_required',
        label: '是否必填',
        type: 'checkbox',
        required: false
      }
    ]
  },
  {
    id: 'default_schedules',
    name: 'default_schedules',
    label: '預設時段',
    type: 'array',
    required: false,
    fields: [
      {
        id: 'weekdays',
        name: 'weekdays',
        label: '星期',
        type: 'multi-select',
        options: [
          { value: 0, label: '週日' },
          { value: 1, label: '週一' },
          { value: 2, label: '週二' },
          { value: 3, label: '週三' },
          { value: 4, label: '週四' },
          { value: 5, label: '週五' },
          { value: 6, label: '週六' }
        ],
        required: true
      },
      {
        id: 'start_time',
        name: 'start_time',
        label: '開始時間',
        type: 'time',
        required: true
      },
      {
        id: 'end_time',
        name: 'end_time',
        label: '結束時間',
        type: 'time',
        required: true
      },
      {
        id: 'capacity',
        name: 'capacity',
        label: '人數上限',
        type: 'number',
        required: false
      }
    ]
  }
]

const ServiceManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { reservationItems } = useAppSelector((state) => state.reservation)

  const [selected, setSelected] = useState<number[]>([])
  const [deleteTarget, setDeleteTarget] =
    useState<ReservationItemsResponse | null>(null)
  const [dialogs, setDialogs] = useState({
    create: false,
    deleteSingle: false,
    deleteMulti: false
  })
  const [editTarget, setEditTarget] = useState<ReservationItemsResponse | null>(
    null
  )
  const [editDialogOpen, setEditDialogOpen] = useState(false)

  const [getServices] = useLazyGetServicesQuery()
  const [insertService] = useInsertServiceMutation()
  const [deleteServices] = useDeleteReservationItemsMutation()
  const [patchReservationItem] = usePatchReservationItemMutation()

  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

  useEffect(() => {
    getServices({ bot_uuid: currentBot!.bot_detail_id })
  }, [currentBot, getServices])

  const breadcrumbItems = [
    { link: PAGE_PATHS.BOT_LIST, linkText: t(TEXT.botPageTitle) },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}`,
      linkText: currentBot?.chinese_name ?? ''
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}/${PAGE_PATHS.KNOWLEDGE_MOUDLE}`,
      linkText: t(TEXT.title)
    }
  ]

  const handleCreateService = async (
    data: Omit<
      InsertReservationItemRequest,
      'options' | 'default_schedules'
    > & {
      options?: (NonNullable<
        InsertReservationItemRequest['options']
      >[number] & {
        [key: string]: unknown
      })[]
      default_schedules?: ({
        weekdays: number[]
      } & Omit<
        NonNullable<InsertReservationItemRequest['default_schedules']>[number],
        'weekday'
      >)[]
    }
  ) => {
    try {
      const options = (data.options || []).map(
        (
          option
        ): NonNullable<InsertReservationItemRequest['options']>[number] => ({
          option_name: option.option_name,
          option_description: option.option_description || '',
          price: Number(option.price),
          type: option.type,
          is_required: option.is_required === true,
          is_active: true
        })
      )

      const scheduleMap = new Map<
        number,
        NonNullable<InsertReservationItemRequest['default_schedules']>[number]
      >()

      for (const schedule of data.default_schedules || []) {
        const weekdays = [...new Set(schedule.weekdays || [])] as number[]
        weekdays.forEach((weekday) => {
          scheduleMap.set(weekday, {
            schedule_type: 'weekly',
            weekday,
            start_time: schedule.start_time,
            end_time: schedule.end_time,
            capacity: schedule.capacity ? Number(schedule.capacity) : 1,
            is_closed: false,
            is_active: true
          })
        })
      }

      const payload: InsertReservationItemRequest = {
        bot_uuid: currentBot!.bot_detail_id,
        reservation_name: data.reservation_name,
        reservation_description: data.reservation_description,
        duration_minutes: Number(data.duration_minutes),
        price: Number(data.price),
        options,
        default_schedules: Array.from(scheduleMap.values())
      }

      await insertService(payload).unwrap()
      setDialogs((prev) => ({ ...prev, create: false }))
      getServices({ bot_uuid: currentBot!.bot_detail_id })
    } catch (error) {
      console.error('新增服務失敗', error)
    }
  }

  const handleDelete = async (objectIds: number[]) => {
    await deleteServices({
      bot_uuid: currentBot!.bot_detail_id,
      delete_object_list: objectIds
    }).unwrap()
    getServices({ bot_uuid: currentBot!.bot_detail_id })
  }

  const handleSingleDelete = (item: ReservationItemsResponse) => {
    setDeleteTarget(item)
    setDialogs((prev) => ({ ...prev, deleteSingle: true }))
  }

  type EditFormType = {
    reservation_name: string
    reservation_description: string
    duration_minutes: number
    price: number
    is_active: boolean
    options: ReservationItemOptionUpdate[]
    schedules: ReservationItemScheduleUpdate[]
  }

  const [editForm, setEditForm] = useState<EditFormType | null>(null)

  // 編輯時初始化表單
  const handleEdit = (item: ReservationItemsResponse) => {
    setEditTarget(item)
    setEditForm({
      reservation_name: item.reservation_name ?? '',
      reservation_description: item.reservation_description ?? '',
      duration_minutes: item.duration_minutes ?? 0,
      price: item.price ?? 0,
      is_active: true,
      options: (item.options || []).map(
        (opt): ReservationItemOptionUpdate => ({
          option_id: opt.option_id,
          option_name: opt.option_name ?? '', // 保證 string
          option_description: opt.option_description ?? '',
          price: opt.price ?? 0,
          type: opt.type ?? 'text',
          is_required: opt.is_required ?? false,
          is_active: opt.is_active ?? true
        })
      ),
      schedules: (item.schedules || []).map(
        (sch): ReservationItemScheduleUpdate => ({
          reservation_item_schedule_id: sch.reservation_item_schedule_id,
          schedule_type:
            sch.schedule_type === 'weekly' || sch.schedule_type === 'specific'
              ? sch.schedule_type
              : 'weekly', // fallback 預設
          weekday: sch.weekday,
          schedule_date: sch.schedule_date ?? undefined,
          start_time: sch.start_time ?? '',
          end_time: sch.end_time ?? '',
          capacity: sch.capacity ?? 1,
          is_closed: sch.is_closed ?? false,
          note: sch.note ?? '',
          is_active: sch.is_active ?? true
        })
      )
    })
    setEditDialogOpen(true)
  }

  const handleEditDialogClose = () => {
    setEditDialogOpen(false)
    setEditTarget(null)
  }

  const handleEditFormChange = <K extends keyof EditFormType>(
    field: K,
    value: EditFormType[K]
  ) => {
    setEditForm((prev) => (prev ? { ...prev, [field]: value } : prev))
  }

  // 編輯送出
  const handleEditSubmit = async () => {
    if (!editTarget || !editForm) return
    try {
      const fixedOptions = editForm.options.map(
        (opt: ReservationItemOptionUpdate): ReservationItemOptionUpdate => ({
          ...opt,
          option_id:
            typeof opt.option_id === 'string' ? opt.option_id : undefined
        })
      )
      const fixedSchedules = editForm.schedules.map(
        (
          sch: ReservationItemScheduleUpdate
        ): ReservationItemScheduleUpdate => ({
          ...sch,
          reservation_item_schedule_id:
            typeof sch.reservation_item_schedule_id === 'string'
              ? sch.reservation_item_schedule_id
              : undefined
        })
      )

      await patchReservationItem({
        bot_uuid: currentBot!.bot_detail_id,
        object_id: editTarget.object_id,
        detail: {
          reservation_name: editForm.reservation_name,
          reservation_description: editForm.reservation_description,
          duration_minutes: Number(editForm.duration_minutes),
          price: Number(editForm.price),
          is_active: editForm.is_active
        },
        options: fixedOptions,
        schedules: fixedSchedules
      }).unwrap()

      setEditDialogOpen(false)
      setEditTarget(null)
      getServices({ bot_uuid: currentBot!.bot_detail_id })
    } catch {
      alert('更新失敗')
    }
  }

  const columns = [
    { id: 'reservation_name', label: '服務名稱' },
    { id: 'price', label: '價格' },
    { id: 'duration_minutes', label: '時長' },
    { id: 'reservation_description', label: '描述' }
  ]

  return (
    <StyledServiceManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">{t(TEXT.title)}</Typography>
        <Box display="flex" gap={2}>
          {!!selected.length && (
            <Button
              variant="outlined"
              color="error"
              onClick={() => setDialogs((d) => ({ ...d, deleteMulti: true }))}
            >
              {TEXT.deleteButtonText}
            </Button>
          )}
          <Button
            variant="contained"
            onClick={() => setDialogs((d) => ({ ...d, create: true }))}
          >
            新增服務
          </Button>
        </Box>
      </Box>

      <CustomTable
        data={reservationItems}
        columns={columns}
        selected={selected}
        setSelected={setSelected}
        onEdit={handleEdit}
        onDelete={handleSingleDelete}
      />

      <CustomDialog
        fullScreen
        maxWidth="xl"
        open={dialogs.create}
        title="新增服務"
        fields={createFields}
        handleClose={() => setDialogs((d) => ({ ...d, create: false }))}
        onSubmit={handleCreateService}
      />

      <CustomDialog
        open={dialogs.deleteSingle}
        title={t(TEXT.deleteSingleTitle, {
          name: deleteTarget?.reservation_name ?? ''
        })}
        handleClose={() => setDialogs((d) => ({ ...d, deleteSingle: false }))}
        onSubmit={() => {
          handleDelete([deleteTarget!.object_id])
          setDialogs((d) => ({ ...d, deleteSingle: false }))
          setDeleteTarget(null)
        }}
      />

      <CustomDialog
        open={dialogs.deleteMulti}
        title={t(TEXT.deleteMultiTitle)}
        handleClose={() => setDialogs((d) => ({ ...d, deleteMulti: false }))}
        onSubmit={() => {
          const ids = selected
            .map((i) => reservationItems[i]?.object_id)
            .filter(Boolean)
          handleDelete(ids)
          setSelected([])
          setDialogs((d) => ({ ...d, deleteMulti: false }))
        }}
      />

      {/* Edit Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={handleEditDialogClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>編輯預約資料</DialogTitle>
        <DialogContent dividers>
          {editForm && (
            <Box
              component="form"
              sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
            >
              <TextField
                label="服務名稱"
                value={editForm.reservation_name}
                onChange={(e) =>
                  handleEditFormChange('reservation_name', e.target.value)
                }
                fullWidth
              />
              <TextField
                label="描述"
                value={editForm.reservation_description}
                onChange={(e) =>
                  handleEditFormChange(
                    'reservation_description',
                    e.target.value
                  )
                }
                fullWidth
              />
              <TextField
                label="價格"
                type="number"
                value={editForm.price}
                onChange={(e) =>
                  handleEditFormChange('price', Number(e.target.value))
                }
              />
              <TextField
                label="時長（分鐘）"
                type="number"
                value={editForm.duration_minutes}
                onChange={(e) =>
                  handleEditFormChange(
                    'duration_minutes',
                    Number(e.target.value)
                  )
                }
              />
              <Typography variant="subtitle1" sx={{ mt: 2 }}>
                選項
              </Typography>
              <OptionEditor
                options={editForm.options}
                onChange={(opts) => handleEditFormChange('options', opts)}
              />
              <Typography variant="subtitle1" sx={{ mt: 2 }}>
                預設時段
              </Typography>
              <ScheduleEditor
                schedules={editForm.schedules}
                onChange={(schedules) =>
                  handleEditFormChange('schedules', schedules)
                }
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleEditDialogClose}>取消</Button>
          <Button
            onClick={handleEditSubmit}
            variant="contained"
            color="primary"
          >
            儲存
          </Button>
        </DialogActions>
      </Dialog>
    </StyledServiceManagementPage>
  )
}

export default ServiceManagementPage
