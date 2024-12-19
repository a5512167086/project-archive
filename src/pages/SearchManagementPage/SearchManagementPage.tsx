import { CustomTable } from '@/components/CustomTable'
import { StyledSearchManagementPage } from './SearchManagementPage.style'
import { Box, Button, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import {
  SearchItem,
  useDeleteSearchItemsMutation,
  useLazyGetSearchItemsQuery
} from '@/store/apis/searchApi'
import { useAppSelector } from '@/utils/hook'
import { getBotClassId, isEmpty } from '@/utils/helper'
import { useEffect, useState } from 'react'
import { CustomDialog } from '@/components/CustomDialog'

const searchManagementPageContent = {
  title: 'searchSettingPage.title',
  addButtonText: 'searchSettingPage.addSearchItemButton',
  deleteButtonText: 'searchSettingPage.deleteSelectedSearchItems',
  deleteDialogTitle: 'searchSettingPage.deleteSearchItemTitle',
  deleteMutiDialogTitle: 'searchSettingPage.deleteSearchItemsTitle'
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
  const botClassId = getBotClassId(botList, currentBotObjectId!)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isMutiDialogOpen, setIsMutiDialogOpen] = useState(false)
  const [selected, setSelected] = useState<number[]>([])
  const [currentDeleteSearchItem, setCurrentDeleteSearchItem] =
    useState<SearchItem | null>(null)
  const [getSearchItems] = useLazyGetSearchItemsQuery()
  const [deleteSearchItems] = useDeleteSearchItemsMutation()

  const handleMutiDialogClose = () => {
    setIsMutiDialogOpen(false)
  }

  const handleMutiDialogConfirm = () => {
    const deletedIdList = selected.map((index) => searchItems[index]?.object_id)

    deleteSearchItems({
      bot_class_id: botClassId,
      deleted_id_list: deletedIdList
    }).then(() => {
      setSelected([])
      getSearchItems({ bot_class_id: botClassId })
    })
  }

  const handleDelteItems = () => {
    setIsMutiDialogOpen(true)
  }

  const handleDeleteItem = (item: SearchItem) => {
    setCurrentDeleteSearchItem(item)
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setCurrentDeleteSearchItem(null)
    setIsDialogOpen(false)
  }

  const handleDialogConfirm = () => {
    deleteSearchItems({
      bot_class_id: botClassId,
      deleted_id_list: [currentDeleteSearchItem!.object_id!]
    }).then(() => {
      getSearchItems({ bot_class_id: botClassId })
    })
  }

  useEffect(() => {
    getSearchItems({ bot_class_id: botClassId })
  }, [botList, currentBotObjectId])

  return (
    <StyledSearchManagementPage disableGutters maxWidth={false}>
      <Box className="search__titleBox">
        <Typography variant="h5" className="search__title">
          {t(searchManagementPageContent.title)}
        </Typography>
        <Box>
          {!isEmpty(selected) && (
            <Button
              className="search__deleteButton"
              variant="outlined"
              color="error"
              onClick={handleDelteItems}
              disabled={isEmpty(selected)}
            >
              {t(searchManagementPageContent.deleteButtonText)}
            </Button>
          )}
          <Button variant="outlined">
            {t(searchManagementPageContent.addButtonText)}
          </Button>
        </Box>
      </Box>
      <CustomTable
        data={searchItems}
        columns={columns}
        onDelete={(item) => {
          handleDeleteItem(item)
        }}
        onEdit={(item) => {
          console.log(item)
        }}
        selected={selected}
        setSelected={setSelected}
      />
      <CustomDialog
        isOpen={isDialogOpen}
        title={t(searchManagementPageContent.deleteDialogTitle, {
          item_name:
            currentDeleteSearchItem && currentDeleteSearchItem.chinese_name
        })}
        handleClose={handleDialogClose}
        onSubmit={handleDialogConfirm}
      />
      <CustomDialog
        isOpen={isMutiDialogOpen}
        handleClose={handleMutiDialogClose}
        title={t(searchManagementPageContent.deleteMutiDialogTitle)}
        onSubmit={handleMutiDialogConfirm}
      />
    </StyledSearchManagementPage>
  )
}
