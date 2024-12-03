import { Typography } from '@mui/material'
import { StyledNotFoundPage } from './NotFoundPage.style'
import ErrorIcon from '@/assets/error-404.png'
import { useTranslation } from 'react-i18next'

const notFoundPage = {
  title: 'notFoundPage.title',
  description: 'notFoundPage.description'
}

export const NotFoundPage = () => {
  const { t } = useTranslation()
  return (
    <StyledNotFoundPage>
      <img className="notfound__errorImg" src={ErrorIcon} />
      <Typography variant="h5" className="notfound__title">
        {t(notFoundPage.title)}
      </Typography>
      <Typography variant="h6" className="notfound__description">
        {t(notFoundPage.description)}
      </Typography>
    </StyledNotFoundPage>
  )
}
