import { CustomTable } from '@/components/CustomTable'
import { StyledSearchManagementPage } from './SearchManagementPage.style'
import { Box, Button, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useLazyGetSearchItemsQuery } from '@/store/apis/searchApi'
import { useAppSelector } from '@/utils/hook'
import { getBotClassId } from '@/utils/helper'
import { useEffect } from 'react'

const searchManagementPageContent = {
  title: 'searchSettingPage.title',
  addButtonText: 'searchSettingPage.addSearchItemButton'
}

const columns = [
  { id: 'chinese_name', label: '中文名稱' },
  { id: 'english_name', label: '英文名稱' },
  { id: 'type', label: '類型' }
]

export const SearchManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { searchItems } = useAppSelector((state) => state.search)
  const [getSearchItems] = useLazyGetSearchItemsQuery()

  useEffect(() => {
    const botClassId = getBotClassId(botList, currentBotObjectId!)
    getSearchItems({ bot_class_id: botClassId })
  }, [botList, currentBotObjectId])

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
      <CustomTable
        data={searchItems}
        columns={columns}
        onDelete={(item) => {
          console.log(item)
        }}
        onEdit={(item) => {
          console.log(item)
        }}
      />
    </StyledSearchManagementPage>
  )
}
