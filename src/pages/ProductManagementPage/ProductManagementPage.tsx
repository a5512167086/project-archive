import { useState } from 'react'
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

// 模擬數據
const initialBrands: Brand[] = [
  { id: '1', name: 'Apple', description: '蘋果公司' },
  { id: '2', name: 'Samsung', description: '三星電子' },
  { id: '3', name: 'Sony', description: '索尼公司' }
]

const initialCategories: Category[] = [
  {
    id: '1',
    name: '電子產品',
    description: '各種電子設備',
    children: [
      {
        id: '2',
        name: '手機',
        description: '智慧型手機',
        parentId: '1',
        children: [
          { id: '3', name: 'iPhone', description: '蘋果手機', parentId: '2' },
          { id: '4', name: 'Android', description: '安卓手機', parentId: '2' }
        ]
      },
      {
        id: '5',
        name: '電腦',
        description: '個人電腦',
        parentId: '1',
        children: [
          {
            id: '6',
            name: '筆記型電腦',
            description: '便攜式電腦',
            parentId: '5'
          },
          {
            id: '7',
            name: '桌上型電腦',
            description: '桌面電腦',
            parentId: '5'
          }
        ]
      }
    ]
  },
  {
    id: '8',
    name: '家電',
    description: '家用電器',
    children: [
      { id: '9', name: '冰箱', description: '冷藏設備', parentId: '8' },
      { id: '10', name: '洗衣機', description: '洗滌設備', parentId: '8' }
    ]
  }
]

const initialProducts: Product[] = [
  {
    id: '1',
    name: 'iPhone 15 Pro',
    description: '最新款iPhone',
    price: 35900,
    brandId: '1',
    categoryId: '3',
    stock: 50,
    status: 'active'
  },
  {
    id: '2',
    name: 'Galaxy S24',
    description: '三星旗艦手機',
    price: 28900,
    brandId: '2',
    categoryId: '4',
    stock: 30,
    status: 'active'
  },
  {
    id: '3',
    name: 'MacBook Pro',
    description: '蘋果筆記型電腦',
    price: 65900,
    brandId: '1',
    categoryId: '6',
    stock: 20,
    status: 'active'
  }
]

const ProductManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)

  const [activeTab, setActiveTab] = useState(0)

  // 數據狀態
  const [brands, setBrands] = useState<Brand[]>(initialBrands)
  const [categories, setCategories] = useState<Category[]>(initialCategories)
  const [products, setProducts] = useState<Product[]>(initialProducts)
  const [expandedCategories, setExpandedCategories] = useState<string[]>([
    '1',
    '2',
    '5',
    '8'
  ])

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
    parentId: ''
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
            onCategoriesChange={setCategories}
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
