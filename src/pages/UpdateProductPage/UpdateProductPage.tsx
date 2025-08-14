import { StyledUpdateProductPage } from './UpdateProductPage.style'
import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppSelector } from '@/utils/hook'
import { ProductVariantManagement } from './ProductVariantManagement'
import { ProductImageManagement } from './ProductImageManagement'
import {
  useLazyGetProductsQuery,
  useUpdateProductMutation,
  GetProductsResponse
} from '@/store/apis/productApi'
import { useLazyGetBrandsQuery } from '@/store/apis/brandApi'
import { useLazyGetCategoriesQuery } from '@/store/apis/categoryApi'
import { useTranslation } from 'react-i18next'
import { flattenCategories } from '@/utils/helper'
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  Button,
  Tabs,
  Tab,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  SelectChangeEvent,
  Grid2,
  CircularProgress
} from '@mui/material'
import { showSuccessToast } from '@/utils/toast'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
type FormState = {
  product_name: string
  product_description: string | null | ''
  sku_code: string | null
  brand_id: number | string | null
  category_id: number | string | null
  price: number | null
  stock: number | null
  is_active: boolean
}

const initialFormState: FormState = {
  product_name: '',
  product_description: '',
  sku_code: '',
  brand_id: null,
  category_id: null,
  price: null,
  stock: null,
  is_active: true
}
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
    defaultValue: null
  },
  {
    id: 'category_id',
    name: 'category_id',
    label: 'productManagementPage.category',
    type: 'select',
    required: true,
    options: [], // will be filled dynamically
    defaultValue: null
  },
  {
    id: 'price',
    name: 'price',
    label: 'productManagementPage.price',
    type: 'number',
    required: true,
    defaultValue: null
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
    id: 'is_active',
    name: 'is_active',
    label: 'productManagementPage.active',
    type: 'checkbox',
    required: false,
    defaultValue: true
  }
]

const UpdateProductPage = () => {
  const { t } = useTranslation()
  const { productId } = useParams<{ productId: string }>()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const navigate = useNavigate()
  const { products } = useAppSelector((state) => state.product)
  const { brandList } = useAppSelector((state) => state.brand)
  const { categoryList } = useAppSelector((state) => state.category)
  const [product, setProduct] = useState<GetProductsResponse | null>(null)
  const [formData, setFormData] = useState<FormState>(initialFormState)
  const [getProducts] = useLazyGetProductsQuery()
  const [getCategories] = useLazyGetCategoriesQuery()
  const [getBrands] = useLazyGetBrandsQuery()
  const [updateProduct] = useUpdateProductMutation()

  useEffect(() => {
    if (currentBot) {
      getProducts({ bot_uuid: currentBot.bot_detail_id })
      getCategories(currentBot.bot_detail_id)
      getBrands(currentBot.bot_detail_id)
    }
  }, [currentBot, getProducts, getCategories, getBrands])

  useEffect(() => {
    if (products.length > 0 && productId) {
      const foundProduct = products.find((p) => p.product_id === productId)
      if (foundProduct) {
        setProduct(foundProduct)
        setFormData({
          ...foundProduct,
          brand_id: foundProduct.brand_id ?? null,
          category_id: foundProduct.category_id ?? null
        })
      }
    }
  }, [products, productId])

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target
    setFormData((prev: FormState) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSelectChange = (event: SelectChangeEvent) => {
    const { name, value } = event.target
    setFormData((prev: FormState) => ({
      ...prev,
      [name]: value
    }))
  }

  const handleVariantsUpdate = () => {
    if (currentBot) {
      getProducts({ bot_uuid: currentBot.bot_detail_id })
    }
  }

  const handleImagesUpdate = () => {
    if (currentBot) {
      getProducts({ bot_uuid: currentBot.bot_detail_id })
    }
  }

  const handleUpdateProduct = async () => {
    if (!product) return

    const submitData = {
      bot_uuid: currentBot!.bot_detail_id,
      product_id: product.product_id,
      product_name: formData.product_name,
      product_description: formData.product_description,
      sku_code: String(formData.sku_code) === '' ? null : formData.sku_code,
      price: Number(formData.price),
      stock:
        formData.stock === null ||
        formData.stock === undefined ||
        String(formData.stock) === '' ||
        isNaN(Number(formData.stock))
          ? null
          : Number(formData.stock),
      is_active: formData.is_active,
      category_id:
        formData.category_id === 'none'
          ? null
          : formData.category_id === null
            ? null
            : Number(formData.category_id),
      brand_id:
        formData.brand_id === 'none'
          ? null
          : formData.brand_id === null
            ? null
            : Number(formData.brand_id)
    }
    await updateProduct(submitData).unwrap()
    showSuccessToast('success.product_updated', t)
    getProducts({ bot_uuid: currentBot!.bot_detail_id })
    navigate(`/bot-list/${currentBot!.bot_detail_id}/product`)
  }

  const [currentTab, setCurrentTab] = useState(0)
  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue)
  }

  const fields = useMemo(() => {
    return updateProductFields.map((field) => {
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
      return field
    })
  }, [brandList, categoryList, t])

  if (!product) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%'
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  return (
    <StyledUpdateProductPage disableGutters maxWidth={false}>
      <Card>
        <CardHeader
          title={`${t('productManagementPage.editProduct')}: ${
            product.product_name
          }`}
          action={
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                onClick={() =>
                  navigate(`/bot-list/${currentBot!.bot_detail_id}/product`)
                }
              >
                {t('common.cancel')}
              </Button>
              <Button variant="contained" onClick={handleUpdateProduct}>
                {t('updateProductPage.updateProductButton')}
              </Button>
            </Box>
          }
        />
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={currentTab} onChange={handleTabChange}>
              <Tab label={t('updateProductPage.productDataTab')} />
              <Tab label={t('updateProductPage.variantsTab')} />
              <Tab label={t('updateProductPage.imagesTab')} />
            </Tabs>
          </Box>
          {currentTab === 0 && (
            <Box component="form" sx={{ mt: 2 }}>
              <Grid2 container spacing={2}>
                {fields.map((field) => (
                  <Grid2 size={{ xs: 12, sm: 6 }} key={field.id}>
                    {field.type === 'text' || field.type === 'number' ? (
                      <TextField
                        fullWidth
                        name={field.name}
                        label={t(field.label)}
                        type={field.type}
                        value={formData[field.name as keyof FormState] ?? ''}
                        onChange={handleFormChange}
                        required={field.required}
                      />
                    ) : field.type === 'select' ? (
                      <FormControl fullWidth>
                        <InputLabel>{t(field.label)}</InputLabel>
                        <Select
                          name={field.name}
                          value={
                            formData[field.name as keyof FormState] === null
                              ? 'none'
                              : String(formData[field.name as keyof FormState])
                          }
                          label={t(field.label)}
                          onChange={handleSelectChange}
                        >
                          {field.options?.map((option) => (
                            <MenuItem key={option.value} value={option.value}>
                              {option.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    ) : field.type === 'checkbox' ? (
                      <FormControlLabel
                        control={
                          <Checkbox
                            name={field.name}
                            checked={Boolean(
                              formData[field.name as keyof FormState]
                            )}
                            onChange={handleFormChange}
                          />
                        }
                        label={t(field.label)}
                      />
                    ) : null}
                  </Grid2>
                ))}
              </Grid2>
            </Box>
          )}
          {currentTab === 1 && (
            <Box
              sx={{ mt: 2, flex: 1, display: 'flex', flexDirection: 'column' }}
            >
              <ProductVariantManagement
                variants={product.variants || []}
                productId={product.product_id}
                onVariantsUpdate={handleVariantsUpdate}
              />
            </Box>
          )}
          {currentTab === 2 && (
            <Box sx={{ mt: 2 }}>
              <ProductImageManagement
                images={product.images || []}
                productId={product.product_id}
                onImagesUpdate={handleImagesUpdate}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </StyledUpdateProductPage>
  )
}

export default UpdateProductPage
