import React, { useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid2,
  CircularProgress
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { CustomTable } from '@/components/CustomTable'
import {
  useLazyGetBrandsQuery,
  useCreateBrandMutation,
  useUpdateBrandMutation,
  useDeleteBrandMutation,
  type Brand as ApiBrand
} from '@/store/apis/brandApi'
import { useAppSelector } from '@/utils/hook'
import { CustomDialog } from '@/components/CustomDialog'
import { showSuccessToast } from '@/utils/toast'

interface Brand {
  id: string
  name: string
  description: string
  logo?: string
}

interface BrandForm {
  name: string
  description: string
}

interface BrandManagementProps {
  brands: Brand[]
  selectedBrands: number[]
  brandDialog: boolean
  editingBrand: Brand | null
  brandForm: BrandForm
  onBrandsChange: (brands: Brand[]) => void
  onSelectedBrandsChange: React.Dispatch<React.SetStateAction<number[]>>
  onBrandDialogChange: (open: boolean) => void
  onEditingBrandChange: (brand: Brand | null) => void
  onBrandFormChange: (form: BrandForm) => void
}

const BrandManagement = ({
  brands,
  selectedBrands,
  brandDialog,
  editingBrand,
  brandForm,
  onBrandsChange,
  onSelectedBrandsChange,
  onBrandDialogChange,
  onEditingBrandChange,
  onBrandFormChange
}: BrandManagementProps) => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const { brandList } = useAppSelector((state) => state.brand)
  const [getBrands] = useLazyGetBrandsQuery()
  const [createBrand, { isLoading: isCreating }] = useCreateBrandMutation()
  const [updateBrand, { isLoading: isUpdating }] = useUpdateBrandMutation()
  const [deleteBrand, { isLoading: isDeleting }] = useDeleteBrandMutation()
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)
  const [multiDeleteDialogOpen, setMultiDeleteDialogOpen] =
    React.useState(false)
  const [currentDeleteBrand, setCurrentDeleteBrand] =
    React.useState<Brand | null>(null)

  useEffect(() => {
    if (brandList.length > 0) {
      const convertedBrands: Brand[] = brandList.map((brand: ApiBrand) => ({
        id: brand.object_id.toString(),
        name: brand.brand_name,
        description: brand.brand_description
      }))
      onBrandsChange(convertedBrands)
    } else {
      onBrandsChange([])
    }
  }, [brandList, onBrandsChange])

  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getBrands(currentBot.bot_detail_id)
    }
  }, [currentBot?.bot_detail_id, getBrands])

  const brandColumns = [
    { id: 'name', label: 'productManagementPage.brandName' },
    { id: 'description', label: 'productManagementPage.description' }
  ]

  const handleBrandSubmit = async () => {
    if (!currentBotObjectId) return

    try {
      if (editingBrand) {
        await updateBrand({
          bot_uuid: currentBot!.bot_detail_id,
          object_id: Number(editingBrand.id),
          brand_name: brandForm.name,
          brand_description: brandForm.description
        }).unwrap()
        showSuccessToast(t('success.data_updated'))
        getBrands(currentBot!.bot_detail_id)
      } else {
        await createBrand({
          bot_uuid: currentBot!.bot_detail_id,
          brand_name: brandForm.name,
          brand_description: brandForm.description
        }).unwrap()
        showSuccessToast(t('success.data_saved'))
        getBrands(currentBot!.bot_detail_id)
      }
      onBrandDialogChange(false)
      onBrandFormChange({ name: '', description: '' })
      onEditingBrandChange(null)
    } catch (error) {
      console.error('Brand operation failed:', error)
    }
  }

  const handleDeleteBrandConfirm = async () => {
    if (!currentBotObjectId || !currentDeleteBrand) return
    try {
      await deleteBrand({
        bot_uuid: currentBot!.bot_detail_id,
        deleted_id_list: [Number(currentDeleteBrand.id)]
      }).unwrap()
      showSuccessToast(t('success.data_deleted'))
      getBrands(currentBot!.bot_detail_id)
    } catch (error) {
      console.error('Delete brand failed:', error)
    }
    setDeleteDialogOpen(false)
    setCurrentDeleteBrand(null)
  }

  const deleteBrandItem = (brand: Brand) => {
    setCurrentDeleteBrand(brand)
    setDeleteDialogOpen(true)
  }

  const handleMultiDeleteBrandConfirm = async () => {
    if (!currentBotObjectId || selectedBrands.length === 0) return
    try {
      const selectedBrandIds = selectedBrands.map((index) =>
        Number(brands[index].id)
      )
      await deleteBrand({
        bot_uuid: currentBot!.bot_detail_id,
        deleted_id_list: selectedBrandIds
      }).unwrap()
      showSuccessToast(t('success.data_deleted'))
      getBrands(currentBot!.bot_detail_id)
      onSelectedBrandsChange([])
    } catch (error) {
      console.error('Delete selected brands failed:', error)
    }
    setMultiDeleteDialogOpen(false)
  }

  const handleDeleteSelectedBrands = () => {
    setMultiDeleteDialogOpen(true)
  }

  const handleEditBrand = (brand: Brand) => {
    onEditingBrandChange(brand)
    onBrandFormChange({ name: brand.name, description: brand.description })
    onBrandDialogChange(true)
  }

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0
      }}
    >
      <Card
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
          overflow: 'hidden'
        }}
      >
        <CardHeader
          title={t('productManagementPage.brandManagement')}
          sx={{ flexShrink: 0 }}
          action={
            <Box display="flex" gap={2}>
              {selectedBrands.length > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleDeleteSelectedBrands}
                  disabled={isDeleting}
                >
                  {t('productManagementPage.deleteSelected')}
                </Button>
              )}
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  onEditingBrandChange(null)
                  onBrandFormChange({ name: '', description: '' })
                  onBrandDialogChange(true)
                }}
              >
                {t('productManagementPage.addBrand')}
              </Button>
            </Box>
          }
        />
        <CardContent
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            padding: 2,
            '&:last-child': {
              paddingBottom: 2
            }
          }}
          className="product__tableContainer"
        >
          <CustomTable
            data={brands}
            columns={brandColumns}
            selected={selectedBrands}
            setSelected={onSelectedBrandsChange}
            onEdit={handleEditBrand}
            onDelete={deleteBrandItem}
          />
          {/* 單一刪除確認 Dialog */}
          <CustomDialog
            open={deleteDialogOpen}
            title={t('productManagementPage.deleteSingleTitle', {
              name: currentDeleteBrand?.name || ''
            })}
            handleClose={() => {
              setDeleteDialogOpen(false)
              setTimeout(() => {
                setCurrentDeleteBrand(null)
              }, 200)
            }}
            onSubmit={handleDeleteBrandConfirm}
            dangerButton
          />
          {/* 多選刪除確認 Dialog */}
          <CustomDialog
            open={multiDeleteDialogOpen}
            title={t('productManagementPage.deleteMultiTitle')}
            handleClose={() => setMultiDeleteDialogOpen(false)}
            onSubmit={handleMultiDeleteBrandConfirm}
            dangerButton
          />
        </CardContent>
      </Card>

      {/* 品牌對話框 */}
      <Dialog
        open={brandDialog}
        onClose={() => onBrandDialogChange(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editingBrand
            ? t('productManagementPage.editBrand')
            : t('productManagementPage.addBrand')}
        </DialogTitle>
        <DialogContent>
          <Grid2 container spacing={2} sx={{ mt: 1 }}>
            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label={t('productManagementPage.brandName')}
                value={brandForm.name}
                onChange={(e) =>
                  onBrandFormChange({ ...brandForm, name: e.target.value })
                }
                disabled={isCreating || isUpdating}
              />
            </Grid2>
            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label={t('productManagementPage.brandDescription')}
                multiline
                rows={3}
                value={brandForm.description}
                onChange={(e) =>
                  onBrandFormChange({
                    ...brandForm,
                    description: e.target.value
                  })
                }
                disabled={isCreating || isUpdating}
              />
            </Grid2>
          </Grid2>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => onBrandDialogChange(false)}
            disabled={isCreating || isUpdating}
          >
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleBrandSubmit}
            variant="contained"
            disabled={isCreating || isUpdating || !brandForm.name.trim()}
          >
            {(isCreating || isUpdating) && (
              <CircularProgress size={20} sx={{ mr: 1 }} />
            )}
            {editingBrand ? t('common.update') : t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default BrandManagement
