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
  ReservationItemScheduleUpdate,
  ReservationOptionGroupCreate,
  ReservationItemOptionCreate,
  ReservationItemScheduleCreate
} from '@/store/apis/reservationApi'
import { CustomTable } from '@/components/CustomTable'
import { CustomDialog } from '@/components/CustomDialog'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import { useApiErrorHandler } from '@/hooks/useApiErrorHandler'
import { OptionEditor } from './OptionEditor'
import { ScheduleEditor } from './ScheduleEditor'
import { OptionGroupEditor, OptionGroupData } from './OptionGroupEditor'
import {
  CreateScheduleEditor,
  CreateScheduleData
} from './CreateScheduleEditor'

const TEXT = {
  title: 'serviceManagementPage.title',
  botPageTitle: 'botPage.myBot',
  deleteSingleTitle: '刪除服務「{{name}}」？',
  deleteMultiTitle: '刪除選取的服務？',
  deleteButtonText: '刪除已選取'
} as const

const ServiceManagementPage = () => {
  const { t } = useTranslation()
  const { handleError, showSuccess } = useApiErrorHandler()
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
  const [createOptionGroups, setCreateOptionGroups] = useState<
    OptionGroupData[]
  >([])
  const [createFormData, setCreateFormData] = useState({
    reservation_name: '',
    reservation_description: '',
    duration_minutes: 0,
    price: 0
  })
  const [createSchedules, setCreateSchedules] = useState<CreateScheduleData[]>(
    []
  )

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
      'option_groups' | 'default_schedules'
    > & {
      option_groups?: (ReservationOptionGroupCreate & {
        [key: string]: unknown
      })[]
      default_schedules?: ({
        weekdays: number[]
      } & Omit<ReservationItemScheduleCreate, 'schedule_type' | 'weekday'>)[]
    }
  ) => {
    try {
      const option_groups = (data.option_groups || []).map(
        (group): ReservationOptionGroupCreate => ({
          group_name: group.group_name,
          group_description: group.group_description || null,
          selection_type: group.selection_type as 'single' | 'multiple',
          is_required: group.is_required === true,
          display_order: Number(group.display_order) || 0,
          is_active: true,
          options: (group.options || []).map(
            (option): ReservationItemOptionCreate => ({
              option_name: option.option_name,
              option_description: option.option_description || null,
              price: Number(option.price) || 0,
              display_order: Number(option.display_order) || 0,
              is_active: true
            })
          )
        })
      )

      // Convert weekdays array to individual schedule entries
      const scheduleMap = new Map<number, ReservationItemScheduleCreate>()

      for (const schedule of data.default_schedules || []) {
        const weekdays = [...new Set(schedule.weekdays || [])] as number[]
        weekdays.forEach((weekday) => {
          scheduleMap.set(weekday, {
            schedule_type: 'weekly',
            weekday,
            schedule_date: null,
            start_time: schedule.start_time,
            end_time: schedule.end_time,
            capacity: schedule.capacity ? Number(schedule.capacity) : 1,
            is_closed: false,
            note: null,
            is_active: true,
            latest_reservation_time: null
          })
        })
      }

      const payload: InsertReservationItemRequest = {
        bot_uuid: currentBot!.bot_detail_id,
        reservation_name: data.reservation_name,
        reservation_description: data.reservation_description,
        duration_minutes: Number(data.duration_minutes),
        price: Number(data.price),
        option_groups,
        default_schedules: Array.from(scheduleMap.values())
      }

      await insertService(payload).unwrap()
      showSuccess('success.service_created')
      setDialogs((prev) => ({ ...prev, create: false }))
      getServices({ bot_uuid: currentBot!.bot_detail_id })
    } catch (error) {
      handleError(error)
    }
  }

  const handleDelete = async (objectIds: number[]) => {
    try {
      await deleteServices({
        bot_uuid: currentBot!.bot_detail_id,
        delete_object_list: objectIds
      }).unwrap()

      if (objectIds.length > 1) {
        showSuccess('success.services_deleted')
      } else {
        showSuccess('success.service_deleted')
      }

      getServices({ bot_uuid: currentBot!.bot_detail_id })
    } catch (error) {
      handleError(error)
    }
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

      {/* Create Dialog */}
      <Dialog
        open={dialogs.create}
        onClose={() => {
          setDialogs((d) => ({ ...d, create: false }))
          setCreateOptionGroups([])
          setCreateSchedules([])
          setCreateFormData({
            reservation_name: '',
            reservation_description: '',
            duration_minutes: 0,
            price: 0
          })
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>新增服務</DialogTitle>
        <DialogContent dividers>
          <Box
            component="form"
            sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}
            onSubmit={(e) => {
              e.preventDefault()
              const data = {
                ...createFormData,
                bot_uuid: currentBot!.bot_detail_id,
                option_groups:
                  createOptionGroups as (ReservationOptionGroupCreate & {
                    [key: string]: unknown
                  })[],
                default_schedules: createSchedules
              }
              handleCreateService(data)
            }}
          >
            <TextField
              label="服務名稱"
              name="reservation_name"
              value={createFormData.reservation_name}
              onChange={(e) =>
                setCreateFormData((prev) => ({
                  ...prev,
                  reservation_name: e.target.value
                }))
              }
              required
              fullWidth
            />
            <TextField
              label="描述"
              name="reservation_description"
              value={createFormData.reservation_description}
              onChange={(e) =>
                setCreateFormData((prev) => ({
                  ...prev,
                  reservation_description: e.target.value
                }))
              }
              required
              fullWidth
            />
            <TextField
              label="時長（分鐘）"
              name="duration_minutes"
              type="number"
              value={createFormData.duration_minutes}
              onChange={(e) =>
                setCreateFormData((prev) => ({
                  ...prev,
                  duration_minutes: Number(e.target.value)
                }))
              }
              required
              fullWidth
            />
            <TextField
              label="價格"
              name="price"
              type="number"
              value={createFormData.price}
              onChange={(e) =>
                setCreateFormData((prev) => ({
                  ...prev,
                  price: Number(e.target.value)
                }))
              }
              required
              fullWidth
            />

            {/* Option Groups Editor */}
            <OptionGroupEditor
              optionGroups={createOptionGroups}
              onChange={setCreateOptionGroups}
            />

            {/* Schedule Editor */}
            <CreateScheduleEditor
              schedules={createSchedules}
              onChange={setCreateSchedules}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setDialogs((d) => ({ ...d, create: false }))
              setCreateOptionGroups([])
              setCreateSchedules([])
              setCreateFormData({
                reservation_name: '',
                reservation_description: '',
                duration_minutes: 0,
                price: 0
              })
            }}
          >
            取消
          </Button>
          <Button
            onClick={() => {
              const form = document.querySelector('form')
              if (form) {
                form.dispatchEvent(
                  new Event('submit', { bubbles: true, cancelable: true })
                )
              }
            }}
            variant="contained"
            color="primary"
          >
            建立
          </Button>
        </DialogActions>
      </Dialog>

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
