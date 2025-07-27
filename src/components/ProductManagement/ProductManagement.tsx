import React from 'react'
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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid2
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { CustomTable } from '@/components/CustomTable'

interface Brand {
  id: string
  name: string
  description: string
  logo?: string
}

interface Category {
  id: string
  name: string
  description: string
  parentId?: string
  children?: Category[]
}

interface Product {
  id: string
  name: string
  description: string
  price: number
  brandId: string
  categoryId: string
  stock: number
  status: 'active' | 'inactive'
}

interface ProductForm {
  name: string
  description: string
  price: number
  brandId: string
  categoryId: string
  stock: number
  status: 'active' | 'inactive'
}

interface ProductManagementProps {
  products: Product[]
  brands: Brand[]
  categories: Category[]
  selectedProducts: number[]
  productDialog: boolean
  editingProduct: Product | null
  productForm: ProductForm
  onProductsChange: (products: Product[]) => void
  onSelectedProductsChange: React.Dispatch<React.SetStateAction<number[]>>
  onProductDialogChange: (open: boolean) => void
  onEditingProductChange: (product: Product | null) => void
  onProductFormChange: (form: ProductForm) => void
}

const ProductManagement: React.FC<ProductManagementProps> = ({
  products,
  brands,
  categories,
  selectedProducts,
  productDialog,
  editingProduct,
  productForm,
  onProductsChange,
  onSelectedProductsChange,
  onProductDialogChange,
  onEditingProductChange,
  onProductFormChange
}) => {
  const { t } = useTranslation()

  // 獲取所有類別（扁平化）
  const getAllCategories = (cats: Category[]): Category[] => {
    let result: Category[] = []
    cats.forEach((cat) => {
      result.push(cat)
      if (cat.children) {
        result = result.concat(getAllCategories(cat.children))
      }
    })
    return result
  }

  const allCategories = getAllCategories(categories)

  // 商品表格列定義
  const productColumns = [
    { id: 'name', label: 'productManagementPage.productName' },
    { id: 'brandName', label: 'productManagementPage.brand' },
    { id: 'categoryName', label: 'productManagementPage.category' },
    { id: 'price', label: 'productManagementPage.price' },
    { id: 'stock', label: 'productManagementPage.stock' },
    { id: 'status', label: 'productManagementPage.status' }
  ]

  // 準備商品表格數據
  const productTableData = products.map((product) => {
    const brand = brands.find((b) => b.id === product.brandId)
    const category = allCategories.find((c) => c.id === product.categoryId)
    return {
      ...product,
      brandName: brand?.name || '',
      categoryName: category?.name || '',
      price: `NT$ ${product.price.toLocaleString()}`,
      status: product.status === 'active' ? '啟用' : '停用'
    }
  })

  const handleProductSubmit = () => {
    if (editingProduct) {
      onProductsChange(
        products.map((p) =>
          p.id === editingProduct.id ? { ...editingProduct, ...productForm } : p
        )
      )
    } else {
      onProductsChange([
        ...products,
        { id: Date.now().toString(), ...productForm }
      ])
    }
    onProductDialogChange(false)
    onProductFormChange({
      name: '',
      description: '',
      price: 0,
      brandId: '',
      categoryId: '',
      stock: 0,
      status: 'active'
    })
    onEditingProductChange(null)
  }

  const deleteProduct = (product: (typeof productTableData)[0]) => {
    onProductsChange(products.filter((p) => p.id !== product.id))
  }

  const handleDeleteSelectedProducts = () => {
    const selectedProductIds = selectedProducts.map(
      (index) => products[index].id
    )
    onProductsChange(
      products.filter((product) => !selectedProductIds.includes(product.id))
    )
    onSelectedProductsChange([])
  }

  const handleEditProduct = (product: (typeof productTableData)[0]) => {
    const originalProduct = products.find((p) => p.id === product.id)
    if (originalProduct) {
      onEditingProductChange(originalProduct)
      onProductFormChange({
        name: originalProduct.name,
        description: originalProduct.description,
        price: originalProduct.price,
        brandId: originalProduct.brandId,
        categoryId: originalProduct.categoryId,
        stock: originalProduct.stock,
        status: originalProduct.status
      })
      onProductDialogChange(true)
    }
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
          title={t('productManagementPage.productList')}
          sx={{ flexShrink: 0 }}
          action={
            <Box display="flex" gap={2}>
              {selectedProducts.length > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleDeleteSelectedProducts}
                >
                  {t('productManagementPage.deleteSelected')}
                </Button>
              )}
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  onEditingProductChange(null)
                  onProductFormChange({
                    name: '',
                    description: '',
                    price: 0,
                    brandId: '',
                    categoryId: '',
                    stock: 0,
                    status: 'active'
                  })
                  onProductDialogChange(true)
                }}
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
          className="product__tableContainer"
        >
          <CustomTable
            data={productTableData}
            columns={productColumns}
            selected={selectedProducts}
            setSelected={onSelectedProductsChange}
            onEdit={handleEditProduct}
            onDelete={deleteProduct}
          />
        </CardContent>
      </Card>

      {/* 商品對話框 */}
      <Dialog
        open={productDialog}
        onClose={() => onProductDialogChange(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingProduct
            ? t('productManagementPage.editProduct')
            : t('productManagementPage.addProduct')}
        </DialogTitle>
        <DialogContent>
          <Grid2 container spacing={2} sx={{ mt: 1 }}>
            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label={t('productManagementPage.productName')}
                value={productForm.name}
                onChange={(e) =>
                  onProductFormChange({ ...productForm, name: e.target.value })
                }
              />
            </Grid2>
            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label={t('productManagementPage.productDescription')}
                multiline
                rows={3}
                value={productForm.description}
                onChange={(e) =>
                  onProductFormChange({
                    ...productForm,
                    description: e.target.value
                  })
                }
              />
            </Grid2>
            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label={t('productManagementPage.price')}
                type="number"
                value={productForm.price}
                onChange={(e) =>
                  onProductFormChange({
                    ...productForm,
                    price: Number(e.target.value)
                  })
                }
              />
            </Grid2>
            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label={t('productManagementPage.stock')}
                type="number"
                value={productForm.stock}
                onChange={(e) =>
                  onProductFormChange({
                    ...productForm,
                    stock: Number(e.target.value)
                  })
                }
              />
            </Grid2>
            <Grid2 size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>{t('productManagementPage.brand')}</InputLabel>
                <Select
                  value={productForm.brandId}
                  label={t('productManagementPage.brand')}
                  onChange={(e) =>
                    onProductFormChange({
                      ...productForm,
                      brandId: e.target.value
                    })
                  }
                >
                  {brands.map((brand) => (
                    <MenuItem key={brand.id} value={brand.id}>
                      {brand.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid2>
            <Grid2 size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>{t('productManagementPage.category')}</InputLabel>
                <Select
                  value={productForm.categoryId}
                  label={t('productManagementPage.category')}
                  onChange={(e) =>
                    onProductFormChange({
                      ...productForm,
                      categoryId: e.target.value
                    })
                  }
                >
                  {allCategories.map((category) => (
                    <MenuItem key={category.id} value={category.id}>
                      {category.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid2>
            <Grid2 size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>{t('productManagementPage.status')}</InputLabel>
                <Select
                  value={productForm.status}
                  label={t('productManagementPage.status')}
                  onChange={(e) =>
                    onProductFormChange({
                      ...productForm,
                      status: e.target.value as 'active' | 'inactive'
                    })
                  }
                >
                  <MenuItem value="active">
                    {t('productManagementPage.active')}
                  </MenuItem>
                  <MenuItem value="inactive">
                    {t('productManagementPage.inactive')}
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid2>
          </Grid2>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => onProductDialogChange(false)}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleProductSubmit} variant="contained">
            {editingProduct ? t('common.update') : t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ProductManagement
