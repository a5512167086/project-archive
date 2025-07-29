import { useState, useEffect, useMemo } from 'react'
import {
  useLazyGetProductsQuery,
  useCreateProductsMutation,
  useUpdateProductMutation,
  useDeleteProductsMutation,
  GetProductsResponse,
  CreateProductRequest
} from '@/store/apis/productApi'
import { useAppSelector } from '@/utils/hook'
import { useTranslation } from 'react-i18next'
import { CustomTable } from '@/components/CustomTable'
import { Box, Card, CardHeader, CardContent, Button } from '@mui/material'
import { Add } from '@mui/icons-material'
import { CustomDialog } from '@/components/CustomDialog/CustomDialog'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { showSuccessToast } from '@/utils/toast'
import { isEmpty } from '@/utils/helper'
import { useLazyGetBrandsQuery } from '@/store/apis/brandApi'
import { useLazyGetCategoriesQuery } from '@/store/apis/categoryApi'

const productColumns = [
  { id: 'product_name', label: 'productManagementPage.productName' },
  { id: 'sku_code', label: 'productManagementPage.skuCode' },
  { id: 'price', label: 'productManagementPage.price' },
  { id: 'stock', label: 'productManagementPage.stock' }
]

const createProductFields: FieldProps[] = [
  {
    id: 'product_name',
    name: 'product_name',
    label: 'productManagementPage.productName',
    type: 'text',
    required: true,
    defaultValue: ''
  },
  {
    id: 'product_description',
    name: 'product_description',
    label: 'productManagementPage.productDescription',
    type: 'text',
    required: false,
    defaultValue: ''
  },
  {
    id: 'sku_code',
    name: 'sku_code',
    label: 'productManagementPage.skuCode',
    type: 'text',
    required: true,
    defaultValue: ''
  },
  {
    id: 'brand_id',
    name: 'brand_id',
    label: 'productManagementPage.brand',
    type: 'select',
    required: true,
    options: [], // will be filled dynamically
    defaultValue: 'none' // 預設未選擇
  },
  {
    id: 'category_id',
    name: 'category_id',
    label: 'productManagementPage.category',
    type: 'select',
    required: true,
    options: [], // will be filled dynamically
    defaultValue: 'none' // 預設未選擇
  },
  {
    id: 'price',
    name: 'price',
    label: 'productManagementPage.price',
    type: 'number',
    required: true,
    defaultValue: 0
  },
  {
    id: 'stock',
    name: 'stock',
    label: 'productManagementPage.stock',
    type: 'number',
    required: true,
    defaultValue: 0
  },
  {
    id: 'images',
    name: 'images',
    label: 'productManagementPage.imageUpload',
    type: 'file',
    required: false,
    multiple: true,
    accept: 'image/*',
    defaultValue: null
  },
  {
    id: 'is_active',
    name: 'is_active',
    label: 'productManagementPage.active',
    type: 'checkbox',
    required: false,
    defaultValue: true
  }
]

const updateProductFields: FieldProps[] = [
  {
    id: 'product_name',
    name: 'product_name',
    label: 'productManagementPage.productName',
    type: 'text',
    required: true,
    defaultValue: ''
  },
  {
    id: 'product_description',
    name: 'product_description',
    label: 'productManagementPage.productDescription',
    type: 'text',
    required: false,
    defaultValue: ''
  },
  {
    id: 'sku_code',
    name: 'sku_code',
    label: 'productManagementPage.skuCode',
    type: 'text',
    required: true,
    defaultValue: ''
  },
  {
    id: 'brand_id',
    name: 'brand_id',
    label: 'productManagementPage.brand',
    type: 'select',
    required: true,
    options: [], // will be filled dynamically
    defaultValue: 'none' // 預設未選擇
  },
  {
    id: 'category_id',
    name: 'category_id',
    label: 'productManagementPage.category',
    type: 'select',
    required: true,
    options: [], // will be filled dynamically
    defaultValue: 'none' // 預設未選擇
  },
  {
    id: 'price',
    name: 'price',
    label: 'productManagementPage.price',
    type: 'number',
    required: true,
    defaultValue: 0
  },
  {
    id: 'stock',
    name: 'stock',
    label: 'productManagementPage.stock',
    type: 'number',
    required: true,
    defaultValue: 0
  },
  {
    id: 'is_active',
    name: 'is_active',
    label: 'productManagementPage.active',
    type: 'checkbox',
    required: false,
    defaultValue: true
  }
]

export const ProductManagement = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { products } = useAppSelector((state) => state.product)
  const { brandList } = useAppSelector((state) => state.brand)
  const { categoryList } = useAppSelector((state) => state.category)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [getProducts] = useLazyGetProductsQuery()
  const [getCategories] = useLazyGetCategoriesQuery()
  const [getBrands] = useLazyGetBrandsQuery()
  const [selected, setSelected] = useState<number[]>([])
  const [isInsertDialogOpen, setIsInsertDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingProduct, setEditingProduct] =
    useState<GetProductsResponse | null>(null)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isMutiDeleteDialogOpen, setIsMutiDeleteDialogOpen] = useState(false)
  const [currentDeleteProduct, setCurrentDeleteProduct] =
    useState<GetProductsResponse | null>(null)

  const [createProduct] = useCreateProductsMutation()
  const [updateProduct] = useUpdateProductMutation()
  const [deleteProduct] = useDeleteProductsMutation()

  const genProductFields = (productFields: FieldProps[]) =>
    productFields.map((field) => {
      const fieldValue =
        editingProduct?.[field.name as keyof GetProductsResponse]

      if (field.id === 'brand_id') {
        return {
          ...field,
          options: [
            {
              label: t('productManagementPage.noBrand') || '未選擇',
              value: 'none'
            },
            ...brandList.map((brand) => ({
              label: brand.brand_name,
              value: String(brand.object_id)
            }))
          ],
          ...(fieldValue != null ? { defaultValue: String(fieldValue) } : {})
        }
      }

      if (field.id === 'category_id') {
        return {
          ...field,
          options: [
            {
              label: t('productManagementPage.noCategory') || '未選擇',
              value: 'none'
            },
            ...categoryList.map((cat) => ({
              label: cat.category_name,
              value: String(cat.class_id)
            }))
          ],
          ...(fieldValue != null ? { defaultValue: String(fieldValue) } : {})
        }
      }

      return {
        ...field,
        ...(fieldValue !== undefined ? { defaultValue: fieldValue } : {})
      }
    })

  const createFields = useMemo(
    () => genProductFields(createProductFields),
    [brandList, categoryList, t]
  )

  const updateFields = useMemo(
    () => genProductFields(updateProductFields),
    [brandList, categoryList, editingProduct, t]
  )

  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getProducts({ bot_uuid: currentBot.bot_detail_id })
      getCategories(currentBot.bot_detail_id)
      getBrands(currentBot.bot_detail_id)
    }
  }, [currentBot?.bot_detail_id, getProducts])

  const handleOpenCreate = () => {
    setEditingProduct(null)
    setIsInsertDialogOpen(true)
  }

  const handleOpenClose = () => {
    setIsInsertDialogOpen(false)
  }

  const handleOpenEdit = (product: GetProductsResponse) => {
    setEditingProduct(product)
    setIsEditDialogOpen(true)
  }

  const handleEditClose = () => {
    setIsEditDialogOpen(false)
    setEditingProduct(null)
  }

  const handleInsertProductConfirm = async (
    data: Omit<CreateProductRequest, 'bot_uuid' | 'images'> & {
      images?: File[] | null
    }
  ) => {
    // 處理 brand_id 和 category_id 可為 null
    const submitData = {
      ...data,
      brand_id:
        typeof data.brand_id === 'string' && data.brand_id !== 'none'
          ? Number(data.brand_id)
          : null,
      category_id:
        typeof data.category_id === 'string' && data.category_id !== 'none'
          ? Number(data.category_id)
          : null,
      images: data.images || null
    }
    await createProduct({
      bot_uuid: currentBot!.bot_detail_id,
      ...submitData
    })
      .unwrap()
      .then(() => {
        showSuccessToast(t('success.product_added'))
      })
    getProducts({ bot_uuid: currentBot!.bot_detail_id })
    handleOpenClose()
  }

  const handleEditProductConfirm = async (data: {
    product_name: string
    product_description: string
    sku_code: string
    price: number
    stock: number
    is_active: boolean
    category_id?: number | null
    brand_id?: number | null
  }) => {
    if (!editingProduct) return
    const submitData = {
      bot_uuid: currentBot!.bot_detail_id,
      product_id: editingProduct.product_id,
      product_name: data.product_name,
      product_description: data.product_description,
      sku_code: data.sku_code,
      price: data.price,
      stock: data.stock,
      is_active: data.is_active,
      category_id:
        typeof data.category_id === 'string' && data.category_id !== 'none'
          ? Number(data.category_id)
          : null,
      brand_id:
        typeof data.brand_id === 'string' && data.brand_id !== 'none'
          ? Number(data.brand_id)
          : null
    }
    await updateProduct(submitData).unwrap()
    showSuccessToast(t('success.product_updated'))
    getProducts({ bot_uuid: currentBot!.bot_detail_id })
    handleEditClose()
  }

  // 單一刪除
  const handleDeleteProduct = (product: GetProductsResponse) => {
    setCurrentDeleteProduct(product)
    setIsDeleteDialogOpen(true)
  }
  const handleDeleteDialogClose = () => {
    setIsDeleteDialogOpen(false)
    setTimeout(() => {
      setCurrentDeleteProduct(null)
    }, 200)
  }

  const handleDeleteDialogConfirm = async () => {
    if (!currentDeleteProduct) return
    await deleteProduct({
      bot_uuid: currentBot!.bot_detail_id,
      product_ids: [currentDeleteProduct.product_id]
    }).unwrap()
    showSuccessToast(t('success.product_deleted'))
    getProducts({ bot_uuid: currentBot!.bot_detail_id })
    handleDeleteDialogClose()
  }

  // 多選刪除
  const handleDeleteProducts = () => {
    setIsMutiDeleteDialogOpen(true)
  }

  const handleMutiDeleteDialogClose = () => {
    setIsMutiDeleteDialogOpen(false)
  }

  const handleMutiDeleteDialogConfirm = async () => {
    const deletedIdList = selected.map((index) => products[index]?.product_id)
    await deleteProduct({
      bot_uuid: currentBot!.bot_detail_id,
      product_ids: deletedIdList
    }).unwrap()
    showSuccessToast(t('success.product_deleted'))
    setSelected([])
    getProducts({ bot_uuid: currentBot!.bot_detail_id })
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
          title={t('productManagementPage.title')}
          sx={{ flexShrink: 0 }}
          action={
            <Box display="flex">
              {!isEmpty(selected) && (
                <Button
                  sx={{ marginRight: 1 }}
                  variant="outlined"
                  color="error"
                  onClick={handleDeleteProducts}
                >
                  {t('productManagementPage.deleteSelected')}
                </Button>
              )}
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleOpenCreate}
              >
                {t('productManagementPage.addProduct')}
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
            data={products}
            rowsPerPage={8}
            columns={productColumns}
            selected={selected}
            setSelected={setSelected}
            onEdit={handleOpenEdit}
            onDelete={handleDeleteProduct}
          />
          {/* 新增商品 Dialog */}
          <CustomDialog
            open={isInsertDialogOpen}
            handleClose={handleOpenClose}
            title={t('productManagementPage.addProduct')}
            fields={createFields}
            maxWidth="md"
            onSubmit={handleInsertProductConfirm}
            dangerButton={false}
          />
          {/* 編輯商品 Dialog */}
          {editingProduct && (
            <CustomDialog
              open={isEditDialogOpen}
              handleClose={handleEditClose}
              title={t('productManagementPage.editProduct')}
              fields={updateFields}
              maxWidth="md"
              onSubmit={handleEditProductConfirm}
              dangerButton={false}
            />
          )}
          {/* 單一刪除 Dialog */}
          <CustomDialog
            open={isDeleteDialogOpen}
            title={t('productManagementPage.deleteProductSingleTitle', {
              name: currentDeleteProduct?.product_name
            })}
            handleClose={handleDeleteDialogClose}
            onSubmit={handleDeleteDialogConfirm}
          />
          {/* 多選刪除 Dialog */}
          <CustomDialog
            open={isMutiDeleteDialogOpen}
            title={t('productManagementPage.deleteProductMultiTitle')}
            handleClose={handleMutiDeleteDialogClose}
            onSubmit={handleMutiDeleteDialogConfirm}
          />
        </CardContent>
      </Card>
    </Box>
  )
}
