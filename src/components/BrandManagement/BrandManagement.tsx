import { useState, useEffect } from 'react'
import {
  Brand,
  useLazyGetBrandsQuery,
  useCreateBrandMutation,
  useUpdateBrandMutation,
  useDeleteBrandMutation
} from '@/store/apis/brandApi'
import { useAppSelector } from '@/utils/hook'
import { useTranslation } from 'react-i18next'
import { CustomTable } from '@/components/CustomTable'
import { Box, Card, CardHeader, CardContent, Button } from '@mui/material'
import { Add } from '@mui/icons-material'
import { CustomDialog } from '@/components/CustomDialog/CustomDialog'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { showSuccessToast } from '@/utils/toast'
import { isEmpty } from '@/utils/helper'

const brandColumns = [
  { id: 'brand_name', label: 'productManagementPage.brandName' },
  { id: 'brand_description', label: 'productManagementPage.description' }
]

const createBrandFields: FieldProps[] = [
  {
    id: 'brand_name',
    name: 'brand_name',
    label: 'productManagementPage.brandName',
    type: 'text',
    required: true,
    defaultValue: ''
  },
  {
    id: 'brand_description',
    name: 'brand_description',
    label: 'productManagementPage.brandDescription',
    type: 'text',
    required: false,
    defaultValue: ''
  }
]

export const BrandManagement = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { brandList } = useAppSelector((state) => state.brand)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [getBrands] = useLazyGetBrandsQuery()
  const [selected, setSelected] = useState<number[]>([])
  const [isInsertDialogOpen, setIsInsertDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingBrand, setEditingBrand] = useState<Brand | null>(null)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isMutiDeleteDialogOpen, setIsMutiDeleteDialogOpen] = useState(false)
  const [currentDeleteBrand, setCurrentDeleteBrand] = useState<Brand | null>(
    null
  )

  const [createBrand] = useCreateBrandMutation()
  const [updateBrand] = useUpdateBrandMutation()
  const [deleteBrand] = useDeleteBrandMutation()

  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getBrands(currentBot.bot_detail_id)
    }
  }, [currentBot?.bot_detail_id, getBrands])

  const handleOpenCreate = () => {
    setEditingBrand(null)
    setIsInsertDialogOpen(true)
  }

  const handleOpenClose = () => {
    setIsInsertDialogOpen(false)
  }

  const handleOpenEdit = (brand: Brand) => {
    setEditingBrand(brand)
    setIsEditDialogOpen(true)
  }

  const handleEditClose = () => {
    setIsEditDialogOpen(false)
    setEditingBrand(null)
  }

  const handleEditBrandConfirm = async (data: {
    brand_name: string
    brand_description: string
  }) => {
    if (!editingBrand) return

    await updateBrand({
      bot_uuid: currentBot!.bot_detail_id,
      object_id: editingBrand.object_id,
      ...data
    }).unwrap()

    showSuccessToast(t('success.brand_updated'))
    getBrands(currentBot!.bot_detail_id)
    handleEditClose()
  }

  const handleInsertBrandConfirm = async (data: {
    brand_name: string
    brand_description: string
  }) => {
    console.log(data)
    await createBrand({
      bot_uuid: currentBot!.bot_detail_id,
      ...data
    })
      .unwrap()
      .then(() => {
        showSuccessToast(t('success.brand_added'))
      })
    getBrands(currentBot!.bot_detail_id)
    handleOpenClose()
  }

  // 單一刪除
  const handleDeleteBrand = (brand: Brand) => {
    setCurrentDeleteBrand(brand)
    setIsDeleteDialogOpen(true)
  }
  const handleDeleteDialogClose = () => {
    setIsDeleteDialogOpen(false)
    setTimeout(() => {
      setCurrentDeleteBrand(null)
    }, 200)
  }

  const handleDeleteDialogConfirm = async () => {
    if (!currentDeleteBrand) return
    await deleteBrand({
      bot_uuid: currentBot!.bot_detail_id,
      deleted_id_list: [currentDeleteBrand.object_id]
    }).unwrap()
    showSuccessToast(t('success.brand_deleted'))
    getBrands(currentBot!.bot_detail_id)
    handleDeleteDialogClose()
  }

  // 多選刪除
  const handleDeleteBrands = () => {
    setIsMutiDeleteDialogOpen(true)
  }

  const handleMutiDeleteDialogClose = () => {
    setIsMutiDeleteDialogOpen(false)
  }

  const handleMutiDeleteDialogConfirm = async () => {
    const deletedIdList = selected.map((index) => brandList[index]?.object_id)
    await deleteBrand({
      bot_uuid: currentBot!.bot_detail_id,
      deleted_id_list: deletedIdList
    }).unwrap()
    showSuccessToast(t('success.brand_deleted'))
    setSelected([])
    getBrands(currentBot!.bot_detail_id)
    handleMutiDeleteDialogClose()
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
            <Box display="flex">
              {!isEmpty(selected) && (
                <Button
                  sx={{ marginRight: 1 }}
                  variant="outlined"
                  color="error"
                  onClick={handleDeleteBrands}
                >
                  {t('productManagementPage.deleteSelected')}
                </Button>
              )}
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleOpenCreate}
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
        >
          <CustomTable
            data={brandList}
            rowsPerPage={8}
            columns={brandColumns}
            selected={selected}
            setSelected={setSelected}
            onEdit={handleOpenEdit}
            onDelete={handleDeleteBrand}
          />
          {/* 新增品牌 Dialog */}
          <CustomDialog
            open={isInsertDialogOpen}
            handleClose={handleOpenClose}
            title={t('productManagementPage.addBrand')}
            fields={createBrandFields}
            maxWidth="sm"
            onSubmit={handleInsertBrandConfirm}
            dangerButton={false}
          />
          {/* 編輯品牌 Dialog */}
          {editingBrand && (
            <CustomDialog
              open={isEditDialogOpen}
              handleClose={handleEditClose}
              title={t('productManagementPage.editBrand')}
              fields={createBrandFields.map((field) => ({
                ...field,
                defaultValue: editingBrand[field.name as keyof Brand]
              }))}
              maxWidth="sm"
              onSubmit={handleEditBrandConfirm}
              dangerButton={false}
            />
          )}
          {/* 單一刪除 Dialog */}
          <CustomDialog
            open={isDeleteDialogOpen}
            title={t('productManagementPage.deleteSingleTitle', {
              name: currentDeleteBrand?.brand_name
            })}
            handleClose={handleDeleteDialogClose}
            onSubmit={handleDeleteDialogConfirm}
          />
          {/* 多選刪除 Dialog */}
          <CustomDialog
            open={isMutiDeleteDialogOpen}
            title={t('productManagementPage.deleteMultiTitle')}
            handleClose={handleMutiDeleteDialogClose}
            onSubmit={handleMutiDeleteDialogConfirm}
          />
        </CardContent>
      </Card>
    </Box>
  )
}
