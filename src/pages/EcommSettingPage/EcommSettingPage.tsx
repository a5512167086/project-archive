import { useState, useEffect, useMemo } from 'react'
import {
  StyledEcommSettingPage,
  Title,
  SectionTitle,
  ShippingOptionCard
} from './EcommSettingPage.style'
import {
  useLazyGetEcommSettingsQuery,
  useUpdateEcommSettingsMutation,
  useDeleteEcommShippingMethodMutation,
  ShippingOption
} from '@/store/apis/ecommApi'
import {
  Button,
  FormControlLabel,
  TextField,
  Card,
  CardHeader,
  CardContent,
  Box,
  IconButton,
  Switch,
  Typography
} from '@mui/material'
import { useAppSelector } from '@/utils/hook'
import { CustomDialog } from '@/components/CustomDialog'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { Add, Delete } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { isEmpty } from '@/utils/helper'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { PAGE_PATHS } from '@/routes'
import { CustomLoader } from '@/components/CustomLoader'

export const EcommSettingPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { shippingOptions: initialShippingOptions } = useAppSelector(
    (state) => state.ecomm
  )
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

  const [getEcommSettings] = useLazyGetEcommSettingsQuery()
  const [updateEcommSettings] = useUpdateEcommSettingsMutation()
  const [deleteEcommShippingMethod] = useDeleteEcommShippingMethodMutation()
  const [isLoading, setIsLoading] = useState(false)
  const [shippingOptions, setShippingOptions] = useState<ShippingOption[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<ShippingOption | null>(null)

  useEffect(() => {
    if (currentBot) {
      getEcommSettings(currentBot.bot_detail_id)
    }
  }, [currentBot, getEcommSettings])

  useEffect(() => {
    setShippingOptions(initialShippingOptions ?? [])
  }, [initialShippingOptions])

  const handleShippingOptionChange = (
    index: number,
    field: keyof ShippingOption,
    value: string | number | boolean
  ) => {
    const newOptions = [...shippingOptions]
    newOptions[index] = { ...newOptions[index], [field]: value }
    setShippingOptions(newOptions)
  }

  const handleSave = async () => {
    setIsLoading(true)
    if (currentBot) {
      await updateEcommSettings({
        bot_uuid: currentBot.bot_detail_id,
        shipping_options: shippingOptions
      }).unwrap()
      showSuccessToast('success.settings_saved', t)
    }
    setIsLoading(false)
  }

  const handleDelete = (option: ShippingOption) => {
    setDeleteTarget(option)
    setIsDeleteDialogOpen(true)
  }

  const handleCloseDeleteDialog = () => {
    setIsDeleteDialogOpen(false)
    setDeleteTarget(null)
  }

  const handleDeleteConfirm = async () => {
    if (currentBot && deleteTarget) {
      await deleteEcommShippingMethod({
        bot_uuid: currentBot.bot_detail_id,
        method: deleteTarget.method
      }).unwrap()
      showSuccessToast('success.shipping_method_deleted', t)
      getEcommSettings(currentBot.bot_detail_id)
    }
    handleCloseDeleteDialog()
  }

  const handleOpenCreateDialog = () => {
    setIsCreateDialogOpen(true)
  }

  const handleCloseCreateDialog = () => {
    setIsCreateDialogOpen(false)
  }

  const handleCreateConfirm = (data: {
    method: 'home_delivery' | 'store_pickup'
    fee: string
    is_enabled: boolean
  }) => {
    if (shippingOptions.some((opt) => opt.method === data.method)) {
      showErrorToast(null, t, 'error.shipping_method_exists')
      return
    }
    const newOption: ShippingOption = {
      method: data.method,
      fee: Number(data.fee),
      is_enabled: data.is_enabled
    }
    setShippingOptions([...shippingOptions, newOption])
    handleCloseCreateDialog()
  }

  const createShippingOptionFields: FieldProps[] = useMemo(
    () => [
      {
        id: 'method',
        name: 'method',
        label: 'ecommSettingPage.shippingMethod',
        type: 'select',
        required: true,
        options: [
          {
            value: 'home_delivery',
            label: t('ecommSettingPage.homeDelivery')
          },
          { value: 'store_pickup', label: t('ecommSettingPage.storePickup') }
        ],
        defaultValue: 'home_delivery'
      },
      {
        id: 'fee',
        name: 'fee',
        label: 'ecommSettingPage.fee',
        type: 'number',
        required: true,
        defaultValue: 0
      },
      {
        id: 'is_enabled',
        name: 'is_enabled',
        label: 'ecommSettingPage.enabled',
        type: 'checkbox',
        defaultValue: true
      }
    ],
    [t]
  )

  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: 'botPage.myBot'
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBot?.bot_detail_id}`,
      linkText: currentBot?.chinese_name ?? ''
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBot?.bot_detail_id}/${PAGE_PATHS.ECOMM_SETTING}`,
      linkText: 'ecommSettingPage.title'
    }
  ]

  return (
    <StyledEcommSettingPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Title>{t('ecommSettingPage.title')}</Title>
      <Card>
        <CardHeader
          title={
            <SectionTitle>{t('ecommSettingPage.shippingOptions')}</SectionTitle>
          }
          action={
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleOpenCreateDialog}
            >
              {t('ecommSettingPage.addShippingMethod')}
            </Button>
          }
        />
        <CardContent>
          {isEmpty(shippingOptions) && (
            <Typography color="text.secondary" align="center" sx={{ p: 4 }}>
              {t('ecommSettingPage.noShippingOptions')}
            </Typography>
          )}
          {shippingOptions.map((option, index) => (
            <ShippingOptionCard key={option.method}>
              <Typography className="method-name">
                {option.method === 'home_delivery'
                  ? t('ecommSettingPage.homeDelivery')
                  : t('ecommSettingPage.storePickup')}
              </Typography>
              <TextField
                className="fee-input"
                type="number"
                label={t('ecommSettingPage.fee')}
                size="small"
                value={option.fee}
                onChange={(e) =>
                  handleShippingOptionChange(
                    index,
                    'fee',
                    parseInt(e.target.value) || 0
                  )
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={option.is_enabled}
                    onChange={(e) =>
                      handleShippingOptionChange(
                        index,
                        'is_enabled',
                        e.target.checked
                      )
                    }
                  />
                }
                label={t('ecommSettingPage.enabled')}
              />
              <IconButton
                color="error"
                onClick={() => handleDelete(option)}
                disabled={isLoading}
              >
                <Delete />
              </IconButton>
            </ShippingOptionCard>
          ))}
        </CardContent>
      </Card>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSave}
          disabled={isLoading}
        >
          {isLoading ? <CustomLoader size={24} /> : t('common.saveChanges')}
        </Button>
      </Box>

      <CustomDialog
        open={isCreateDialogOpen}
        handleClose={handleCloseCreateDialog}
        title={t('ecommSettingPage.addShippingMethod')}
        fields={createShippingOptionFields}
        onSubmit={handleCreateConfirm}
      />

      <CustomDialog
        open={isDeleteDialogOpen}
        handleClose={handleCloseDeleteDialog}
        title={t('ecommSettingPage.deleteConfirmationTitle')}
        description={t('ecommSettingPage.deleteConfirmationText', {
          method:
            deleteTarget?.method === 'home_delivery'
              ? t('ecommSettingPage.homeDelivery')
              : t('ecommSettingPage.storePickup')
        })}
        onSubmit={handleDeleteConfirm}
        dangerButton
      />
    </StyledEcommSettingPage>
  )
}

export default EcommSettingPage
