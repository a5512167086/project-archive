import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Typography,
  TextField,
  Switch,
  FormControlLabel
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'
import { PAGE_PATHS } from '@/routes'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { StyledServiceManagementPage } from './ServiceManagementPage.style'
import {
  useLazyGetServicesQuery,
  useInsertServiceMutation,
  useDeleteServicesMutation,
  usePatchServiceMutation,
  InsertServiceRequest,
  ServiceResponse,
  ServiceOptionUpdate,
  ServiceOptionGroupUpdate,
  ServiceScheduleUpdate,
  ServiceOptionGroupCreate,
  ServiceOptionCreate,
  ServiceScheduleCreate
} from '@/store/apis/reservationApi'
import { CustomTable } from '@/components/CustomTable'
import { CustomDialog } from '@/components/CustomDialog'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import { useApiHandler } from '@/hooks/useApiHandler'
import { ScheduleEditor } from './ScheduleEditor'
import { OptionGroupEditor, OptionGroupData } from './OptionGroupEditor'
import {
  CreateScheduleEditor,
  CreateScheduleData
} from './CreateScheduleEditor'

const TEXT = {
  title: 'serviceManagementPage.title',
  botPageTitle: 'botPage.myBot',
  deleteSingleTitle: 'serviceManagementPage.deleteSingleTitle',
  deleteMultiTitle: 'serviceManagementPage.deleteMultiTitle',
  deleteButtonText: 'serviceManagementPage.deleteButtonText'
} as const

const ServiceManagementPage = () => {
  const { t } = useTranslation()
  const { handleError, showSuccess } = useApiHandler()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { services } = useAppSelector((state) => state.reservation)

  const [selected, setSelected] = useState<number[]>([])
  const [deleteTarget, setDeleteTarget] = useState<ServiceResponse | null>(null)
  const [dialogs, setDialogs] = useState({
    create: false,
    deleteSingle: false,
    deleteMulti: false
  })
  const [editTarget, setEditTarget] = useState<ServiceResponse | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [createOptionGroups, setCreateOptionGroups] = useState<
    OptionGroupData[]
  >([])
  const [createFormData, setCreateFormData] = useState({
    service_name: '',
    service_description: '',
    duration_minutes: 0,
    price: 0
  })
  const [createSchedules, setCreateSchedules] = useState<CreateScheduleData[]>(
    []
  )

  const [getServices] = useLazyGetServicesQuery()
  const [insertService] = useInsertServiceMutation()
  const [deleteServices] = useDeleteServicesMutation()
  const [patchService] = usePatchServiceMutation()

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
    data: Omit<InsertServiceRequest, 'option_groups' | 'default_schedules'> & {
      option_groups?: (ServiceOptionGroupCreate & {
        [key: string]: unknown
      })[]
      default_schedules?: ({
        weekdays: number[]
      } & Omit<ServiceScheduleCreate, 'schedule_type' | 'weekday'>)[]
    }
  ) => {
    try {
      const option_groups = (data.option_groups || []).map(
        (group): ServiceOptionGroupCreate => ({
          group_name: group.group_name,
          group_description: group.group_description || null,
          selection_type: group.selection_type as 'single' | 'multiple',
          is_required: group.is_required === true,
          display_order: Number(group.display_order) || 0,
          is_active: true,
          options: (group.options || []).map(
            (option): ServiceOptionCreate => ({
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
      const scheduleMap = new Map<number, ServiceScheduleCreate>()

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
            is_active: true
          })
        })
      }

      const payload: InsertServiceRequest = {
        bot_uuid: currentBot!.bot_detail_id,
        service_name: data.service_name,
        service_description: data.service_description,
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

  const handleDelete = async (objectIds: string[]) => {
    try {
      await deleteServices({
        bot_uuid: currentBot!.bot_detail_id,
        delete_service_list: objectIds
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

  const handleSingleDelete = (item: ServiceResponse) => {
    setDeleteTarget(item)
    setDialogs((prev) => ({ ...prev, deleteSingle: true }))
  }

  type EditFormType = {
    service_name: string
    service_description: string
    duration_minutes: number
    price: number
    is_active: boolean
    option_groups: (ServiceOptionGroupUpdate & {
      [key: string]: unknown
    })[]
    schedules: ServiceScheduleUpdate[]
  }

  const [editForm, setEditForm] = useState<EditFormType | null>(null)

  // 編輯時初始化表單
  const handleEdit = (item: ServiceResponse) => {
    setEditTarget(item)

    // 處理 option_groups 結構
    const convertedOptionGroups: ServiceOptionGroupUpdate[] = (
      item.option_groups || []
    ).map(
      (group): ServiceOptionGroupUpdate => ({
        option_group_id: group.option_group_id,
        group_name: group.group_name ?? '',
        group_description: group.group_description ?? '',
        selection_type: group.selection_type ?? 'single',
        is_required: group.is_required ?? false,
        display_order: group.display_order ?? 0,
        is_active: group.is_active ?? true,
        options: (group.options || []).map(
          (opt): ServiceOptionUpdate => ({
            option_id: opt.option_id,
            option_name: opt.option_name ?? '',
            option_description: opt.option_description ?? '',
            price: opt.price ?? 0,
            display_order: opt.display_order ?? 0,
            is_active: opt.is_active ?? true
          })
        )
      })
    )

    setEditForm({
      service_name: item.service_name ?? '',
      service_description: item.service_description ?? '',
      duration_minutes: item.duration_minutes ?? 0,
      price: item.price ?? 0,
      is_active: item.is_active ?? true,
      option_groups: convertedOptionGroups,
      schedules: (item.schedules || []).map(
        (sch): ServiceScheduleUpdate => ({
          reservation_service_schedule_id: sch.service_schedule_id,
          schedule_type: sch.schedule_type,
          weekday: sch.weekday,
          schedule_date: sch.schedule_date ?? undefined,
          start_time: sch.start_time ?? '',
          end_time: sch.end_time ?? '',
          capacity: sch.capacity ?? 1,
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
    const fixedOptionGroups = editForm.option_groups.map(
      (group: ServiceOptionGroupUpdate): ServiceOptionGroupUpdate => ({
        ...group,
        option_group_id:
          typeof group.option_group_id === 'string'
            ? group.option_group_id
            : undefined,
        options: (group.options || []).map(
          (opt): ServiceOptionUpdate => ({
            ...opt,
            option_id:
              typeof opt.option_id === 'string' ? opt.option_id : undefined
          })
        )
      })
    )

    const fixedSchedules = editForm.schedules.map(
      (sch: ServiceScheduleUpdate): ServiceScheduleUpdate => ({
        ...sch,
        reservation_service_schedule_id:
          typeof sch.reservation_service_schedule_id === 'string'
            ? sch.reservation_service_schedule_id
            : undefined
      })
    )

    await patchService({
      bot_uuid: currentBot!.bot_detail_id,
      service_id: editTarget.service_id,
      detail: {
        service_name: editForm.service_name,
        service_description: editForm.service_description,
        duration_minutes: Number(editForm.duration_minutes),
        price: Number(editForm.price),
        is_active: editForm.is_active
      },
      option_groups: fixedOptionGroups,
      schedules: fixedSchedules
    }).unwrap()

    setEditDialogOpen(false)
    setEditTarget(null)
    getServices({ bot_uuid: currentBot!.bot_detail_id })
  }

  const columns = [
    { id: 'service_name', label: t('serviceManagementPage.serviceName') },
    { id: 'price', label: t('common.price') },
    {
      id: 'duration_minutes',
      label: t('serviceManagementPage.durationMinutes')
    },
    { id: 'service_description', label: t('common.description') }
  ]

  return (
    <StyledServiceManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box className="service__titleBox">
        <Typography variant="h5" className='service__title'>{t(TEXT.title)}</Typography>
        <Box display="flex" gap={2}>
          {!!selected.length && (
            <Button
              variant="outlined"
              color="error"
              onClick={() => setDialogs((d) => ({ ...d, deleteMulti: true }))}
            >
              {t(TEXT.deleteButtonText)}
            </Button>
          )}
          <Button
            variant="contained"
            onClick={() => setDialogs((d) => ({ ...d, create: true }))}
          >
            {t('serviceManagementPage.addService')}
          </Button>
        </Box>
      </Box>

      <div className="service__tableContainer">
        <CustomTable
          data={services}
          columns={columns}
          selected={selected}
          setSelected={setSelected}
          onEdit={handleEdit}
          onDelete={handleSingleDelete}
        />
      </div>

      {/* Create Dialog */}
      <Dialog
        open={dialogs.create}
        onClose={() => {
          setDialogs((d) => ({ ...d, create: false }))
          setCreateOptionGroups([])
          setCreateSchedules([])
          setCreateFormData({
            service_name: '',
            service_description: '',
            duration_minutes: 0,
            price: 0
          })
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>{t('serviceManagementPage.addService')}</DialogTitle>
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
                  createOptionGroups as (ServiceOptionGroupCreate & {
                    [key: string]: unknown
                  })[],
                default_schedules: createSchedules
              }
              handleCreateService(data)
            }}
          >
            <TextField
              label={t('serviceManagementPage.serviceName')}
              name="service_name"
              value={createFormData.service_name}
              onChange={(e) =>
                setCreateFormData((prev) => ({
                  ...prev,
                  service_name: e.target.value
                }))
              }
              required
              fullWidth
            />
            <TextField
              label={t('common.description')}
              name="service_description"
              value={createFormData.service_description}
              onChange={(e) =>
                setCreateFormData((prev) => ({
                  ...prev,
                  service_description: e.target.value
                }))
              }
              required
              fullWidth
            />
            <TextField
              label={t('serviceManagementPage.durationMinutes')}
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
              label={t('common.price')}
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
                service_name: '',
                service_description: '',
                duration_minutes: 0,
                price: 0
              })
            }}
          >
            {t('common.cancel')}
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
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      <CustomDialog
        open={dialogs.deleteSingle}
        title={t(TEXT.deleteSingleTitle, {
          name: deleteTarget?.service_name ?? ''
        })}
        handleClose={() => setDialogs((d) => ({ ...d, deleteSingle: false }))}
        onSubmit={() => {
          handleDelete([deleteTarget!.service_id])
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
            .map((i) => services[i]?.service_id)
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
        <DialogTitle>
          {t('serviceManagementPage.editReservationData')}
        </DialogTitle>
        <DialogContent dividers>
          {editForm && (
            <Box
              component="form"
              sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
            >
              <TextField
                label={t('serviceManagementPage.serviceName')}
                value={editForm.service_name}
                onChange={(e) =>
                  handleEditFormChange('service_name', e.target.value)
                }
                fullWidth
              />
              <TextField
                label={t('common.description')}
                value={editForm.service_description}
                onChange={(e) =>
                  handleEditFormChange('service_description', e.target.value)
                }
                fullWidth
              />
              <TextField
                label={t('common.price')}
                type="number"
                value={editForm.price}
                onChange={(e) =>
                  handleEditFormChange('price', Number(e.target.value))
                }
              />
              <TextField
                label={t('serviceManagementPage.durationMinutes')}
                type="number"
                value={editForm.duration_minutes}
                onChange={(e) =>
                  handleEditFormChange(
                    'duration_minutes',
                    Number(e.target.value)
                  )
                }
              />

              {/* Service Active Status */}
              <Box
                sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}
              >
                <Typography variant="subtitle1">
                  {t('serviceManagementPage.serviceStatus')}:
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={editForm.is_active}
                      onChange={(e) =>
                        handleEditFormChange('is_active', e.target.checked)
                      }
                    />
                  }
                  label={
                    editForm.is_active
                      ? t('common.active')
                      : t('common.inactive')
                  }
                />
              </Box>

              <OptionGroupEditor
                optionGroups={editForm.option_groups.map(
                  (group): OptionGroupData => ({
                    group_name: group.group_name || '',
                    group_description: group.group_description || '',
                    selection_type:
                      (group.selection_type as 'single' | 'multiple') ||
                      'single',
                    is_required: group.is_required || false,
                    display_order: group.display_order || 0,
                    is_active: group.is_active !== false,
                    options: (group.options || []).map((opt) => ({
                      option_name: opt.option_name || '',
                      option_description: opt.option_description || '',
                      price: opt.price || 0,
                      display_order: opt.display_order || 0,
                      is_active: opt.is_active !== false
                    }))
                  })
                )}
                onChange={(groups) =>
                  handleEditFormChange(
                    'option_groups',
                    groups.map(
                      (group): ServiceOptionGroupUpdate => ({
                        group_name: group.group_name,
                        group_description: group.group_description,
                        selection_type: group.selection_type,
                        is_required: group.is_required,
                        display_order: group.display_order,
                        is_active: group.is_active,
                        options: group.options.map(
                          (opt): ServiceOptionUpdate => ({
                            option_name: opt.option_name,
                            option_description: opt.option_description,
                            price: opt.price,
                            display_order: opt.display_order,
                            is_active: opt.is_active
                          })
                        )
                      })
                    )
                  )
                }
              />
              <Typography variant="subtitle1" sx={{ mt: 2 }}>
                {t('serviceManagementPage.defaultSchedule')}
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
          <Button onClick={handleEditDialogClose}>{t('common.cancel')}</Button>
          <Button
            onClick={handleEditSubmit}
            variant="contained"
            color="primary"
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </StyledServiceManagementPage>
  )
}

export default ServiceManagementPage
