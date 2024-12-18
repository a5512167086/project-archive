import { CustomTable } from '@/components/CustomTable'
import { StyledSearchManagementPage } from './SearchManagementPage.style'
import { Box, Button, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

const searchManagementPageContent = {
  title: 'searchSettingPage.title',
  addButtonText: 'searchSettingPage.addSearchItemButton'
}

export const SearchManagementPage = () => {
  const { t } = useTranslation()
  return (
    <StyledSearchManagementPage disableGutters maxWidth={false}>
      <Box className="search__titleBox">
        <Typography variant="h5" className="search__title">
          {t(searchManagementPageContent.title)}
        </Typography>
        <Button variant="outlined">
          {t(searchManagementPageContent.addButtonText)}
        </Button>
      </Box>
      <CustomTable />
    </StyledSearchManagementPage>
  )
}
