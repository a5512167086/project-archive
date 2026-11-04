import { Typography } from '@mui/material'
import { StyledNotFoundPage } from './NotFoundPage.style'
import ErrorIcon from '@/assets/error-404.png'
import { useTranslation } from 'react-i18next'

const notFoundPage = {
  title: 'notFoundPage.title',
  description: 'notFoundPage.description'
}

const NotFoundPage = () => {
  const { t } = useTranslation()
  return (
    <StyledNotFoundPage>
      <img
        src={ErrorIcon}
        style={{
          maxWidth: '300px',
          margin: '20px 0'
        }}
      />
      <Typography
        variant="h5"
        sx={{
          margin: '10px 0 ',
          fontSize: '2.25rem',
          fontWeight: 'bold'
        }}
      >
        {t(notFoundPage.title)}
      </Typography>
      <Typography variant="h6">{t(notFoundPage.description)}</Typography>
    </StyledNotFoundPage>
  )
}

export default NotFoundPage
