import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  useLazyGetProductsQuery,
  useCreateProductsMutation,
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
import { flattenCategories } from '@/utils/helper'

const productColumns = [
  { id: 'product_name', label: 'productManagementPage.productName' },
  { id: 'brand_name', label: 'productManagementPage.brand' },
  { id: 'category_name', label: 'productManagementPage.category' },
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
    required: false,
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
    required: false,
    defaultValue: null
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

export const ProductManagement = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { uuid } = useParams<{ uuid: string }>()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const { products } = useAppSelector((state) => state.product)
  const { brandList } = useAppSelector((state) => state.brand)
  const { categoryList } = useAppSelector((state) => state.category)
  const [getProducts] = useLazyGetProductsQuery()
  const [getCategories] = useLazyGetCategoriesQuery()
  const [getBrands] = useLazyGetBrandsQuery()
  const [selected, setSelected] = useState<number[]>([])
  const [isInsertDialogOpen, setIsInsertDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isMutiDeleteDialogOpen, setIsMutiDeleteDialogOpen] = useState(false)
  const [currentDeleteProduct, setCurrentDeleteProduct] =
    useState<GetProductsResponse | null>(null)

  const [createProduct] = useCreateProductsMutation()
  const [deleteProduct] = useDeleteProductsMutation()

  const genProductFields = (productFields: FieldProps[]) =>
    productFields.map((field) => {
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
          ]
        }
      }

      if (field.id === 'category_id') {
        const flattenedCategories = flattenCategories(categoryList, '  ') // Use 2 spaces for indentation
        return {
          ...field,
          options: [
            {
              label: t('productManagementPage.noCategory') || '未選擇',
              value: 'none'
            },
            ...flattenedCategories
          ]
        }
      }

      return {
        ...field
      }
    })

  const createFields = useMemo(
    () => genProductFields(createProductFields),
    [brandList, categoryList, t]
  )

  const tableData = useMemo(() => {
    return products.map((product) => {
      const brand = brandList.find(
        (brand) => brand.object_id === product.brand_id
      )
      const category = categoryList.find(
        (category) => category.class_id === product.category_id
      )
      return {
        ...product,
        brand_name: brand?.brand_name || t('productManagementPage.noBrand'),
        category_name:
          category?.category_name || t('productManagementPage.noCategory')
      }
    })
  }, [products, brandList, categoryList, t])

  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getProducts({ bot_uuid: currentBot.bot_detail_id })
      getCategories(currentBot.bot_detail_id)
      getBrands(currentBot.bot_detail_id)
    }
  }, [currentBot?.bot_detail_id, getProducts])

  const handleOpenCreate = () => {
    setIsInsertDialogOpen(true)
  }

  const handleOpenClose = () => {
    setIsInsertDialogOpen(false)
  }

  const handleOpenEdit = (product: GetProductsResponse) => {
    navigate(`/bot-list/${uuid}/product/${product.product_id}`)
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
        showSuccessToast('success.product_added', t)
      })
    getProducts({ bot_uuid: currentBot!.bot_detail_id })
    handleOpenClose()
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
    showSuccessToast('success.product_deleted', t)
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
    showSuccessToast('success.product_deleted', t)
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
            data={tableData}
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
