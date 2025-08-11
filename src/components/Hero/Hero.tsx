import HeroBackground from '@/assets/bot_img.jpg'
import { StyledHero } from './Hero.style'
import { Box, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

const heroContent = {
  title: 'homePage.hero.title',
  subtitle: 'homePage.hero.subtitle',
  description: 'homePage.hero.description'
}

export const Hero = () => {
  const { t } = useTranslation()

  return (
    <StyledHero maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          maxWidth: '400px',
          height: 'fit-content',
          border: '1px solid lightgray',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: 'rgba(0, 0, 0, 0.1) 0px 10px 50px'
        }}
      >
        <img
          src={HeroBackground}
          alt=""
          loading="lazy"
          style={{
            width: '100%',
            height: 'auto',
            objectFit: 'cover'
          }}
        />
      </Box>
      <Box className="hero__textBox">
        <Typography
          variant="h6"
          sx={(theme) => ({
            fontSize: '1.75rem',
            fontWeight: 'bold',
            marginBottom: '10px',
            [theme.breakpoints.down('md')]: {
              fontSize: '1.5rem'
            }
          })}
        >
          {t(heroContent.title)}
          <br />
          {t(heroContent.subtitle)}
        </Typography>
        <Typography
          variant="h6"
          sx={(theme) => ({
            [theme.breakpoints.down('md')]: {
              fontSize: '1rem'
            }
          })}
        >
          {t(heroContent.description)}
        </Typography>
      </Box>
    </StyledHero>
  )
}
