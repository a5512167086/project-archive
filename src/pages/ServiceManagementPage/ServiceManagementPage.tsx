import { useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid2
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'
import { PAGE_PATHS } from '@/routes'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { StyledServiceManagementPage } from './ServiceManagementPage.style'
import { useLazyGetServicesQuery } from '@/store/apis/reservationApi'
import { getBotClassId } from '@/utils/helper'
import { useNavigate } from 'react-router-dom'

const serviceManagementPageContent = {
  title: 'serviceManagementPage.title',
  botPageTitle: 'botPage.myBot'
}

const ServiceManagementPage = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { reservationItems } = useAppSelector((state) => state.reservation)
  const [getServices] = useLazyGetServicesQuery()
  const botClassId = getBotClassId(botList, currentBotObjectId!)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

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

  useEffect(() => {
    getServices({ bot_class_id: botClassId })
  }, [])

  return (
    <StyledServiceManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />

      <Box
        className="reservation__titleBox"
        display="flex"
        justifyContent="space-between"
        alignItems="center"
      >
        <Typography variant="h4">
          {t(serviceManagementPageContent.title)}
        </Typography>
        <Button
          variant="contained"
          onClick={() => navigate(`/bot/${currentBotObjectId}/services/new`)}
        >
          新增服務
        </Button>
      </Box>

      {reservationItems.length === 0 && (
        <Typography mt={4}>目前尚無任何服務，請新增一項服務。</Typography>
      )}

      <Grid2 container spacing={3}>
        {reservationItems.map((service) => (
          <Grid2 size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={service.object_id}>
            <Card
              variant="outlined"
              sx={{ borderRadius: 3, boxShadow: 1, height: '100%' }}
            >
              <CardContent>
                <Box
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                >
                  <Typography variant="h6" fontWeight="bold">
                    {service.reservation_name}
                  </Typography>
                  <Chip
                    label={`$${service.price}`}
                    color="primary"
                    variant="outlined"
                  />
                </Box>
                <Typography color="text.secondary" mt={0.5}>
                  {service.reservation_description}
                </Typography>
                <Typography mt={1} fontSize={14}>
                  ⏱ 時長：{service.duration_minutes} 分鐘
                </Typography>

                <Divider sx={{ my: 1.5 }} />

                <Typography variant="subtitle2" fontWeight="bold">
                  選項：
                </Typography>
                {service.options.map((opt) => (
                  <Typography
                    key={opt.option_id}
                    fontSize={14}
                    ml={1.5}
                    mt={0.5}
                  >
                    • {opt.option_name}（+${opt.price}）
                    {opt.option_description
                      ? ` - ${opt.option_description}`
                      : ''}
                  </Typography>
                ))}

                <Box mt={2}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    預約時段：
                  </Typography>
                  {service.schedules.map((s) => (
                    <Typography
                      key={s.reservation_item_schedule_id}
                      fontSize={14}
                      ml={1.5}
                      mt={0.5}
                    >
                      •{' '}
                      {s.schedule_type === 'weekly'
                        ? `每週${s.weekday !== null ? ['日', '一', '二', '三', '四', '五', '六'][s.weekday] : ''}`
                        : `特定日期：${s.schedule_date}`}{' '}
                      {s.start_time} ~ {s.end_time}，最多 {s.capacity} 人
                    </Typography>
                  ))}
                </Box>

                <Box textAlign="right" mt={3}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() =>
                      navigate(
                        `/bot/${currentBotObjectId}/services/${service.object_id}`
                      )
                    }
                  >
                    編輯
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid2>
        ))}
      </Grid2>
    </StyledServiceManagementPage>
  )
}

export default ServiceManagementPage
