import { useEffect, useState } from 'react'
import { Box, Button, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'
import { PAGE_PATHS } from '@/routes'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { StyledServiceManagementPage } from './ServiceManagementPage.style'
import { useLazyGetServicesQuery } from '@/store/apis/reservationApi'
import { getBotClassId } from '@/utils/helper'
import { CustomTable } from '@/components/CustomTable'
import { CustomDialog } from '@/components/CustomDialog'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'

const serviceManagementPageContent = {
  title: 'serviceManagementPage.title',
  botPageTitle: 'botPage.myBot'
}

const ServiceManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { reservationItems } = useAppSelector((state) => state.reservation)
  const [getServices] = useLazyGetServicesQuery()
  const [selected, setSelected] = useState<number[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)

  const botClassId = getBotClassId(botList, currentBotObjectId!)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

  useEffect(() => {
    getServices({ bot_class_id: botClassId })
  }, [])

  const columns = [
    { id: 'reservation_name', label: '服務名稱' },
    { id: 'price', label: '價格' },
    { id: 'duration_minutes', label: '時長' },
    { id: 'reservation_description', label: '描述' }
  ]

  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: t(serviceManagementPageContent.botPageTitle)
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}`,
      linkText: currentBot?.bot_name ?? ''
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}/${PAGE_PATHS.KNOWLEDGE_MOUDLE}`,
      linkText: t(serviceManagementPageContent.title)
    }
  ]

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
          id: 'weekday',
          name: 'weekday',
          label: '星期 (0~6)',
          type: 'number',
          required: false
        },
        {
          id: 'start_time',
          name: 'start_time',
          label: '開始時間 (HH:mm)',
          type: 'time',
          required: true
        },
        {
          id: 'end_time',
          name: 'end_time',
          label: '結束時間 (HH:mm)',
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

  const handleCreateService = (data: Record<string, unknown>) => {
    // insertNewReservationItem({
    //   bot_class_id: botClassId,
    //   reservation_name: data.reservation_name as string,
    //   price: Number(data.price),
    //   reservation_description: data.reservation_description as string,
    //   duration_minutes: Number(data.duration_minutes),
    //   options: data.options || [],
    //   schedules: data.schedules || []
    // })
    console.log('Creating service with data:', data)
    getServices({ bot_class_id: botClassId })
  }

  return (
    <StyledServiceManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">
          {t(serviceManagementPageContent.title)}
        </Typography>
        <Button variant="contained" onClick={() => setIsCreateDialogOpen(true)}>
          新增服務
        </Button>
      </Box>
      <CustomTable
        data={reservationItems}
        columns={columns}
        selected={selected}
        setSelected={setSelected}
        onEdit={() => {}}
      />

      <CustomDialog
        fullScreen
        maxWidth="xl"
        handleClose={() => setIsCreateDialogOpen(false)}
        title="新增服務"
        fields={createFields}
        open={isCreateDialogOpen}
        onSubmit={handleCreateService}
      />
    </StyledServiceManagementPage>
  )
}

export default ServiceManagementPage
