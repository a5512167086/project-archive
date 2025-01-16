import { Grid2 } from '@mui/material'
import { StyledBotManagementPage } from './BotManagementPage.style'
import { CustomCard } from '@/components/CustomCard'
import { ActionType } from '@/components/CustomCard/CustomCard.type'
import SettingsIcon from '@mui/icons-material/Settings'
import FAQIcon from '@/assets/faq_icon.png'
import EcommIcon from '@/assets/ecomm_icon.png'
import ReservaitonIcon from '@/assets/reservation_icon.png'
import SearchIcon from '@/assets/search_icon.png'
import { PAGE_PATHS } from '@/routes'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'
import {
  useGetModuleSettingsQuery,
  useInsertModuleSettingMutation
} from '@/store/apis/moduleApi'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'

const modulePageContent = {
  botPageTitle: 'botPage.myBot',
  title: 'botPage.myModule',
  faqTitle: 'common.feature.faqTitle',
  ecommTitle: 'common.feature.ecommTitle',
  reservationTitle: 'common.feature.reservationTitle',
  searchTitle: 'common.feature.searchTitle',
  enable: 'common.enable'
}

const moduleData = [
  {
    moduleName: modulePageContent.faqTitle,
    moduleImg: FAQIcon,
    databaseName: 'FAQ'
  },
  {
    moduleName: modulePageContent.ecommTitle,
    moduleImg: EcommIcon,
    databaseName: 'Ecomm'
  },
  {
    moduleName: modulePageContent.reservationTitle,
    moduleImg: ReservaitonIcon,
    databaseName: 'Reservation'
  },
  {
    moduleName: modulePageContent.searchTitle,
    moduleImg: SearchIcon,
    databaseName: 'Search'
  }
]

const BotManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { moduleSettings } = useAppSelector((state) => state.module)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const { refetch: refreshModuleSettings } = useGetModuleSettingsQuery({
    bot_class_id: currentBot!.class_id
  })
  const [insertModuleSetting, { isLoading }] = useInsertModuleSettingMutation()
  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: modulePageContent.botPageTitle
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBotObjectId}`,
      linkText: currentBot!.bot_name
    }
  ]

  const getCheckedStatus = (moduleName: string): boolean => {
    const module = moduleSettings.find(
      (setting) => setting.chinese_name === moduleName
    )
    return module ? module.is_enabled : false
  }

  const handleModuleOnCheck = async (
    moduleName: string,
    isEnabled: boolean
  ) => {
    if (isLoading) {
      return
    }

    await insertModuleSetting({
      bot_class_id: currentBot!.class_id,
      module_name: moduleName,
      is_enabled: isEnabled
    })
      .unwrap()
      .then(() => {
        refreshModuleSettings()
      })
  }

  return (
    currentBot && (
      <StyledBotManagementPage>
        <CustomBreadcrumb items={breadcrumbItems} />
        <Grid2 container spacing={4}>
          {moduleData.map((module) => (
            <Grid2
              size={{ xs: 12, sm: 6, md: 4 }}
              display="flex"
              justifyContent="center"
              key={module.moduleName}
            >
              <CustomCard
                imgSrc={module.moduleImg}
                cardButton={false}
                titleText={t(module.moduleName)}
                actionType={ActionType.Switch}
                buttonText={t(modulePageContent.enable)}
                buttonIcon={<SettingsIcon />}
                checked={getCheckedStatus(module.databaseName)}
                onSwitchClick={async (checked) => {
                  await handleModuleOnCheck(module.databaseName, checked)
                }}
              />
            </Grid2>
          ))}
        </Grid2>
      </StyledBotManagementPage>
    )
  )
}

export default BotManagementPage
