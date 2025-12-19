import { useState, useMemo } from 'react'
import {
  useCreateProductsVariantsMutation,
  useUpdateProductsVariantsMutation,
  useDeleteProductsVariantsMutation,
  ProductVariantResponse
} from '@/store/apis/productApi'
import { useTranslation } from 'react-i18next'
import { TFunction } from 'i18next'
import { CustomTable } from '@/components/CustomTable'
import { Box, Button } from '@mui/material'
import { Add } from '@mui/icons-material'
import { CustomDialog } from '@/components/CustomDialog/CustomDialog'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { showSuccessToast } from '@/utils/toast'
import { useAppSelector } from '@/utils/hook'
import { useParams } from 'react-router-dom'

type ProductVariantManagementProps = {
  variants: ProductVariantResponse[]
  productId: string
  onVariantsUpdate: () => void
}

type VariantFormData = {
  variant_name: string
  sku_code: string
  price: string
  stock: string
}

const variantColumns = [
  { id: 'variant_name', label: 'productVariant.variantName' },
  { id: 'sku_code', label: 'productVariant.skuCode' },
  { id: 'price', label: 'productVariant.price' },
  { id: 'stock', label: 'productVariant.stock' }
]

const getVariantFields = (t: TFunction): FieldProps[] => [
  {
    id: 'variant_name',
    name: 'variant_name',
    label: t('productVariant.variantName'),
    type: 'text',
    required: true
  },
  {
    id: 'sku_code',
    name: 'sku_code',
    label: t('productVariant.skuCode'),
    type: 'text'
  },
  {
    id: 'price',
    name: 'price',
    label: t('productVariant.price'),
    type: 'number'
  },
  {
    id: 'stock',
    name: 'stock',
    label: t('productVariant.stock'),
    type: 'number'
  }
]

export const ProductVariantManagement = ({
  variants,
  productId,
  onVariantsUpdate
}: ProductVariantManagementProps) => {
  const { t } = useTranslation()
  const { uuid } = useParams()
  const { botList } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.bot_detail_id === uuid)
  const [selected, setSelected] = useState<number[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [selectedVariant, setSelectedVariant] =
    useState<ProductVariantResponse | null>(null)
  const [createVariant] = useCreateProductsVariantsMutation()
  const [updateVariant] = useUpdateProductsVariantsMutation()
  const [deleteVariant] = useDeleteProductsVariantsMutation()

  const handleCreate = async (data: VariantFormData) => {
    const submitData = {
      ...data,
      sku_code: data.sku_code === '' ? null : data.sku_code,
      price:
        data.price === '' || isNaN(Number(data.price))
          ? null
          : Number(data.price),
      stock:
        data.stock === '' || isNaN(Number(data.stock))
          ? null
          : Number(data.stock)
    }
    await createVariant({
      ...submitData,
      bot_uuid: currentBot!.bot_detail_id,
      product_id: productId
    }).unwrap()
    showSuccessToast('success.variant_added', t)
    onVariantsUpdate()
    setIsCreateDialogOpen(false)
  }

  const handleUpdate = async (data: VariantFormData) => {
    if (!selectedVariant) return
    const submitData = {
      ...data,
      sku_code: data.sku_code === '' ? null : data.sku_code,
      price:
        data.price === '' || isNaN(Number(data.price))
          ? null
          : Number(data.price),
      stock:
        data.stock === '' || isNaN(Number(data.stock))
          ? null
          : Number(data.stock)
    }
    await updateVariant({
      ...submitData,
      bot_uuid: currentBot!.bot_detail_id,
      variant_id: selectedVariant.variant_id
    }).unwrap()
    showSuccessToast('success.variant_updated', t)
    onVariantsUpdate()
    setIsEditDialogOpen(false)
    setSelectedVariant(null)
  }

  const handleDelete = async () => {
    if (!selectedVariant) return
    await deleteVariant({
      bot_uuid: currentBot!.bot_detail_id,
      variant_ids: [selectedVariant.variant_id]
    }).unwrap()
    showSuccessToast('success.variant_deleted', t)
    onVariantsUpdate()
    setIsDeleteDialogOpen(false)
    setSelectedVariant(null)
  }

  const variantFields = useMemo(() => getVariantFields(t), [t])

  const editFields = useMemo(() => {
    return getVariantFields(t).map((field) => ({
      ...field,
      defaultValue:
        selectedVariant?.[field.name as keyof ProductVariantResponse] ?? ''
    }))
  }, [selectedVariant, t])

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1
      }}
    >
      <Button
        variant="contained"
        startIcon={<Add />}
        onClick={() => setIsCreateDialogOpen(true)}
        sx={{ mb: 2, alignSelf: 'flex-start' }}
      >
        {t('productVariant.addVariant')}
      </Button>
      <Box
        sx={{
          flex: 1, // 讓表格容器占滿剩餘空間
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        <CustomTable
          columns={variantColumns}
          data={variants}
          selected={selected}
          setSelected={setSelected}
          onEdit={(variant: ProductVariantResponse) => {
            const originalVariant = variants.find(
              (v) => v.variant_id === variant.variant_id
            )
            setSelectedVariant(originalVariant || null)
            setIsEditDialogOpen(true)
          }}
          onDelete={(variant: ProductVariantResponse) => {
            const originalVariant = variants.find(
              (v) => v.variant_id === variant.variant_id
            )
            setSelectedVariant(originalVariant || null)
            setIsDeleteDialogOpen(true)
          }}
        />
      </Box>
      <CustomDialog
        open={isCreateDialogOpen}
        handleClose={() => setIsCreateDialogOpen(false)}
        title={t('productVariant.createVariant')}
        fields={variantFields}
        onSubmit={handleCreate}
      />
      {selectedVariant && (
        <CustomDialog
          open={isEditDialogOpen}
          handleClose={() => {
            setIsEditDialogOpen(false)
            setSelectedVariant(null)
          }}
          title={t('productVariant.editVariant')}
          fields={editFields}
          onSubmit={handleUpdate}
        />
      )}
      {selectedVariant && (
        <CustomDialog
          open={isDeleteDialogOpen}
          handleClose={() => {
            setIsDeleteDialogOpen(false)
            setSelectedVariant(null)
          }}
          title={t('productVariant.deleteVariantTitle', {
            name: selectedVariant.variant_name
          })}
          onSubmit={handleDelete}
        />
      )}
    </Box>
  )
}
