import { Breadcrumbs, Grid2 } from '@mui/material'
import { StyledBotManagementPage } from './BotManagementPage.style'
import { CustomCard } from '@/components/CustomCard'
import { ActionType } from '@/components/CustomCard/CustomCard.type'
import SettingsIcon from '@mui/icons-material/Settings'
import FAQIcon from '@/assets/faq_icon.png'
import EcommIcon from '@/assets/ecomm_icon.png'
import ReservaitonIcon from '@/assets/reservation_icon.png'
import { CustomLink } from '@/components/CustomLink'
import { PAGE_PATHS } from '@/routes'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'

const modulePageContent = {
  botPageTitle: 'botPage.myBot',
  title: 'botPage.myModule',
  faqTitle: 'common.feature.faqTitle',
  ecommTitle: 'common.feature.ecommTitle',
  reservationTitle: 'common.feature.reservationTitle',
  enable: 'common.enable'
}

const moduleData = [
  { moduleName: modulePageContent.faqTitle, moduleImg: FAQIcon },
  { moduleName: modulePageContent.ecommTitle, moduleImg: EcommIcon },
  { moduleName: modulePageContent.reservationTitle, moduleImg: ReservaitonIcon }
]

export const BotManagementPage = () => {
  const { t } = useTranslation()
  const { currentBot } = useAppSelector((state) => state.bot)

  return (
    currentBot && (
      <StyledBotManagementPage>
        <Breadcrumbs
          sx={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '20px 0' }}
        >
          <CustomLink
            link={PAGE_PATHS.BOT_LIST}
            linkText={t(modulePageContent.botPageTitle)}
          />
          <CustomLink
            link={PAGE_PATHS.BOT_LIST + `/${currentBot.object_id}`}
            linkText={currentBot!.bot_name}
            color="text.primary"
            aria-current="page"
          />
        </Breadcrumbs>
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
                enableHeaderButton={true}
                cardButton={false}
                titleText={t(module.moduleName)}
                actionType={ActionType.Switch}
                buttonText={t(modulePageContent.enable)}
                buttonIcon={<SettingsIcon />}
              />
            </Grid2>
          ))}
        </Grid2>
      </StyledBotManagementPage>
    )
  )
}
