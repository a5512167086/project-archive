import { useEffect, useState } from 'react'
import { Box, Typography, Tabs, Tab } from '@mui/material'
import {
  Inventory as InventoryIcon,
  Category as CategoryIcon,
  Business as BusinessIcon
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import TabPanel from '@/components/TabPanel'
import ProductManagement from '@/components/ProductManagement'
import CategoryManagement from '@/components/CategoryManagement'
import BrandManagement from '@/components/BrandManagement'
import { StyledProductManagementPage } from './ProductManagementPage.style'
import { PAGE_PATHS } from '@/routes'
import { useAppSelector } from '@/utils/hook'
import { useLazyGetCategoriesQuery } from '@/store/apis/categoryApi'
import { Category as ApiCategory } from '@/store/apis/categoryApi'

// 類型定義
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

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`
  }
}



const ProductManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { categoryList } = useAppSelector((state) => state.category)
  const [getCategories] = useLazyGetCategoriesQuery()
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

  const [activeTab, setActiveTab] = useState(0)

  // 數據狀態
  const [brands, setBrands] = useState<Brand[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [expandedCategories, setExpandedCategories] = useState<string[]>([])

  // 選擇狀態
  const [selectedProducts, setSelectedProducts] = useState<number[]>([])
  const [selectedBrands, setSelectedBrands] = useState<number[]>([])

  // 品牌管理狀態
  const [brandDialog, setBrandDialog] = useState(false)
  const [editingBrand, setEditingBrand] = useState<Brand | null>(null)
  const [brandForm, setBrandForm] = useState({ name: '', description: '' })

  // 類別管理狀態
  const [categoryDialog, setCategoryDialog] = useState(false)
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    description: '',
    parentId: '0'
  })

  // 商品管理狀態
  const [productDialog, setProductDialog] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: 0,
    brandId: '',
    categoryId: '',
    stock: 0,
    status: 'active' as 'active' | 'inactive'
  })

  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getCategories(currentBot.bot_detail_id)
    }
  }, [currentBot?.bot_detail_id, getCategories])

  const transformApiCategories = (apiCategories: ApiCategory[]): Category[] => {
    return apiCategories.map((cat) => ({
      id: cat.class_id.toString(),
      name: cat.category_name,
      description: cat.category_description,
      parentId: cat.parent_class_id?.toString(),
      children: cat.children ? transformApiCategories(cat.children) : []
    }))
  }

  const getExpandedIds = (categories: Category[]): string[] => {
    const ids: string[] = []
    const traverse = (cats: Category[]) => {
      for (const cat of cats) {
        if (cat.children && cat.children.length > 0) {
          ids.push(cat.id)
          traverse(cat.children)
        }
      }
    }
    traverse(categories)
    return ids
  }

  useEffect(() => {
    if (categoryList) {
      const transformed = transformApiCategories(categoryList)
      setCategories(transformed)
      setExpandedCategories(getExpandedIds(transformed))
    }
  }, [categoryList])

  const breadcrumbItems = [
    { link: PAGE_PATHS.BOT_LIST, linkText: 'botPage.myBot' },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}`,
      linkText: currentBot?.chinese_name ?? ''
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}/product`,
      linkText: 'productManagementPage.title'
    }
  ]

  return (
    <StyledProductManagementPage
      disableGutters
      maxWidth={false}
      sx={{
        height: 'calc(100vh - 64px)', // 減去 header 高度
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minHeight: 0
      }}
    >
      <CustomBreadcrumb items={breadcrumbItems} />

      <Box className="product__titleBox">
        <Typography variant="h5" className="product__title">
          {t('productManagementPage.title')}
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', flexShrink: 0 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          aria-label="product management tabs"
        >
          <Tab
            icon={<InventoryIcon />}
            label={t('productManagementPage.productTab')}
            iconPosition="start"
            {...a11yProps(0)}
          />
          <Tab
            icon={<CategoryIcon />}
            label={t('productManagementPage.categoryTab')}
            iconPosition="start"
            {...a11yProps(1)}
          />
          <Tab
            icon={<BusinessIcon />}
            label={t('productManagementPage.brandTab')}
            iconPosition="start"
            {...a11yProps(2)}
          />
        </Tabs>
      </Box>

      <Box sx={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {/* 商品管理 */}
        <TabPanel value={activeTab} index={0}>
          <ProductManagement
            products={products}
            brands={brands}
            categories={categories}
            selectedProducts={selectedProducts}
            productDialog={productDialog}
            editingProduct={editingProduct}
            productForm={productForm}
            onProductsChange={setProducts}
            onSelectedProductsChange={setSelectedProducts}
            onProductDialogChange={setProductDialog}
            onEditingProductChange={setEditingProduct}
            onProductFormChange={setProductForm}
          />
        </TabPanel>

        {/* 類別管理 */}
        <TabPanel value={activeTab} index={1}>
          <CategoryManagement
            categories={categories}
            expandedCategories={expandedCategories}
            categoryDialog={categoryDialog}
            editingCategory={editingCategory}
            categoryForm={categoryForm}
            onExpandedCategoriesChange={setExpandedCategories}
            onCategoryDialogChange={setCategoryDialog}
            onEditingCategoryChange={setEditingCategory}
            onCategoryFormChange={setCategoryForm}
          />
        </TabPanel>

        {/* 品牌管理 */}
        <TabPanel value={activeTab} index={2}>
          <BrandManagement
            brands={brands}
            selectedBrands={selectedBrands}
            brandDialog={brandDialog}
            editingBrand={editingBrand}
            brandForm={brandForm}
            onBrandsChange={setBrands}
            onSelectedBrandsChange={setSelectedBrands}
            onBrandDialogChange={setBrandDialog}
            onEditingBrandChange={setEditingBrand}
            onBrandFormChange={setBrandForm}
          />
        </TabPanel>
      </Box>
    </StyledProductManagementPage>
  )
}

export default ProductManagementPage
