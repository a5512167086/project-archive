import { useTranslation } from 'react-i18next'
import { StyledCreateBotTutorialPage } from './CreateBotTutorialPage.style'
import { Box, Button, Typography } from '@mui/material'
import step1 from '@/assets/tutorial/step1.png'
import step2 from '@/assets/tutorial/step2.png'
import step3 from '@/assets/tutorial/step3.png'
import step4 from '@/assets/tutorial/step4.png'
import step5 from '@/assets/tutorial/step5.png'
import step6 from '@/assets/tutorial/step6.png'
import step7 from '@/assets/tutorial/step7.png'
import step8 from '@/assets/tutorial/step8.png'
import step9 from '@/assets/tutorial/step9.png'
import { useNavigate } from 'react-router-dom'
import { PAGE_PATHS } from '@/routes'

const createBotTutorialContent = {
  title: 'createBotTutorialPage.title',
  step: 'createBotTutorialPage.step',
  backToBotPage: 'createBotTutorialPage.backToBotPage',
  tutorialContent: [
    { imgSrc: step1, description: 'createBotTutorialPage.step1Description' },
    { imgSrc: step2, description: 'createBotTutorialPage.step2Description' },
    { imgSrc: step3, description: 'createBotTutorialPage.step3Description' },
    { imgSrc: step4, description: 'createBotTutorialPage.step4Description' },
    { imgSrc: step5, description: 'createBotTutorialPage.step5Description' },
    { imgSrc: step6, description: 'createBotTutorialPage.step6Description' },
    { imgSrc: step7, description: 'createBotTutorialPage.step7Description' },
    { imgSrc: step8, description: 'createBotTutorialPage.step8Description' },
    { imgSrc: step9, description: 'createBotTutorialPage.step9Description' }
  ]
}

export const CreateBotTutorialPage = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const handleBackToBotListPage = () => {
    navigate(PAGE_PATHS.BOT_LIST)
  }

  return (
    <StyledCreateBotTutorialPage>
      <Typography variant="h4">{t(createBotTutorialContent.title)}</Typography>
      <Box className="tutorial__link">
        <a href="https://developers.line.biz/zh-hant/">LINE DEVELOPER</a>
        <br />
        <a href="https://tw.linebiz.com/login/">LINE BUSINESS</a>
      </Box>
      {createBotTutorialContent.tutorialContent.map((step, index) => (
        <Box className="tutorial__stepBox" key={index}>
          <Typography variant="h5">
            {t(createBotTutorialContent.step) + (index + 1)}
          </Typography>
          <img className="tutorial__image" src={step.imgSrc} alt="" />
          <Typography variant="h6">{t(step.description)}</Typography>
        </Box>
      ))}
      <Button variant="outlined" onClick={handleBackToBotListPage}>
        {t(createBotTutorialContent.backToBotPage)}
      </Button>
    </StyledCreateBotTutorialPage>
  )
}
