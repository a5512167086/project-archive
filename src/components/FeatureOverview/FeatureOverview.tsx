import { Grid2, Box, Typography } from '@mui/material'
import { StyledFeatureOverview } from './FeatureOverview.style'
import { CustomCard } from '../CustomCard'
import FAQIcon from '@/assets/faq_icon.png'
import EcommIcon from '@/assets/ecomm_icon.png'
import ReservationIcon from '@/assets/reservation_icon.png'
import { useTranslation } from 'react-i18next'

const overviewContent = {
  title: 'homePage.overview.title',
  faqTitle: 'common.feature.faqTitle',
  faqDescription: 'common.feature.faqDescription',
  ecommTitle: 'common.feature.ecommTitle',
  ecommDescription: 'common.feature.ecommDescription',
  reservationTitle: 'common.feature.reservationTitle',
  reservationDescription: 'common.feature.reservationDescription'
}

export const FeatureOverview = () => {
  const { t } = useTranslation()
  return (
    <StyledFeatureOverview maxWidth="xl">
      <Typography className="overview__title" variant="h6">
        {t(overviewContent.title)}
      </Typography>
      <Box className="overview__cardBox">
        <Grid2 container spacing={6}>
          <Grid2
            size={{ xs: 12, md: 6, lg: 4 }}
            display="flex"
            justifyContent="center"
          >
            <CustomCard
              imgSrc={FAQIcon}
              cardButton={false}
              titleText={t(overviewContent.faqTitle)}
              descriptionText={t(overviewContent.faqDescription)}
            />
          </Grid2>
          <Grid2
            size={{ xs: 12, md: 6, lg: 4 }}
            display="flex"
            justifyContent="center"
          >
            <CustomCard
              imgSrc={EcommIcon}
              cardButton={false}
              titleText={t(overviewContent.ecommTitle)}
              descriptionText={t(overviewContent.ecommDescription)}
            />
          </Grid2>
          <Grid2
            size={{ xs: 12, md: 12, lg: 4 }}
            display="flex"
            justifyContent="center"
          >
            <CustomCard
              imgSrc={ReservationIcon}
              cardButton={false}
              titleText={t(overviewContent.reservationTitle)}
              descriptionText={t(overviewContent.reservationDescription)}
            />
          </Grid2>
        </Grid2>
      </Box>
    </StyledFeatureOverview>
  )
}
