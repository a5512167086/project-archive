import { useState } from 'react'
import { Box, Typography, Tabs, Tab } from '@mui/material'
import { Inventory, Category, Business } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import TabPanel from '@/components/TabPanel'
import { StyledProductManagementPage } from './ProductManagementPage.style'
import { PAGE_PATHS } from '@/routes'
import { useAppSelector } from '@/utils/hook'
import { BrandManagement } from '@/components/BrandManagement'
import { CategoryManagement } from '@/components/CategoryManagement'
import { ProductManagement } from '@/components/ProductManagement'

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`
  }
}

const ProductManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [activeTab, setActiveTab] = useState(0)

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

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontSize: '2rem',
            fontWeight: '500'
          }}
        >
          {t('productManagementPage.title')}
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', flexShrink: 0 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          aria-label="product management tabs"
          sx={{ flexShrink: 0 }}
        >
          <Tab
            icon={<Inventory />}
            label={t('productManagementPage.productTab')}
            iconPosition="start"
            {...a11yProps(0)}
          />
          <Tab
            icon={<Category />}
            label={t('productManagementPage.categoryTab')}
            iconPosition="start"
            {...a11yProps(1)}
          />
          <Tab
            icon={<Business />}
            label={t('productManagementPage.brandTab')}
            iconPosition="start"
            {...a11yProps(2)}
          />
        </Tabs>
      </Box>

      <Box sx={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {/* 商品管理 */}
        <TabPanel value={activeTab} index={0}>
          <ProductManagement />
        </TabPanel>

        {/* 類別管理 */}
        <TabPanel value={activeTab} index={1}>
          <CategoryManagement />
        </TabPanel>

        {/* 品牌管理 */}
        <TabPanel value={activeTab} index={2}>
          <BrandManagement />
        </TabPanel>
      </Box>
    </StyledProductManagementPage>
  )
}

export default ProductManagementPage
