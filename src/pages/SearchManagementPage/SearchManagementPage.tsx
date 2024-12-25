import { CustomTable } from '@/components/CustomTable'
import { StyledSearchManagementPage } from './SearchManagementPage.style'
import { Box, Button, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import {
  SearchItem,
  useDeleteSearchItemsMutation,
  useInsertSearchItemMutation,
  useInsertSearchItemsByUrlMutation,
  useLazyGetSearchItemsQuery
} from '@/store/apis/searchApi'
import { useAppSelector } from '@/utils/hook'
import { getBotClassId, isEmpty, isValidHttpUrl } from '@/utils/helper'
import { useEffect, useState } from 'react'
import { CustomDialog } from '@/components/CustomDialog'

const searchManagementPageContent = {
  title: 'searchSettingPage.title',
  addButtonText: 'searchSettingPage.addSearchItemButton',
  addButtonTextByUrl: 'searchSettingPage.addSearchItemFromUrlButton',
  deleteButtonText: 'searchSettingPage.deleteSelectedSearchItems',
  deleteDialogTitle: 'searchSettingPage.deleteSearchItemTitle',
  deleteMutiDialogTitle: 'searchSettingPage.deleteSearchItemsTitle',
  insertByUrlDialogTitle: 'searchSettingPage.insertSearchItemsByUrlTitle'
}

const columns = [
  { id: 'chinese_name', label: '中文名稱' },
  { id: 'english_name', label: '英文名稱' },
  { id: 'type', label: '類型' }
]

const insertSearchItemsByUrlFields = [
  {
    id: 'url',
    name: 'url',
    label: 'common.url',
    type: 'text',
    required: true
  }
]

const insertSingleSearchItemFields = [
  {
    id: 'item_name',
    name: 'item_name',
    label: 'searchSettingPage.itemName',
    type: 'text',
    required: true
  },
  {
    id: 'item_english_name',
    name: 'item_english_name',
    label: 'searchSettingPage.englishName',
    type: 'text'
  },
  { id: 'item_type', name: 'item_type', label: 'Type', type: 'text' },
  {
    id: 'item_description',
    name: 'item_description',
    label: 'common.description',
    type: 'text'
  },
  {
    id: 'item_price',
    name: 'item_price',
    label: 'common.price',
    type: 'text'
  },
  {
    id: 'item_instruction',
    name: 'item_instruction',
    label: 'searchSettingPage.instruction',
    type: 'text'
  },
  {
    id: 'item_ingredient',
    name: 'item_ingredient',
    label: 'searchSettingPage.ingredient',
    type: 'text'
  },
  {
    id: 'item_url',
    name: 'item_url',
    label: 'common.url',
    type: 'text',
    validate: (value: string) => isValidHttpUrl(value)
  }
]

export const SearchManagementPage = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { searchItems } = useAppSelector((state) => state.search)
  const botClassId = getBotClassId(botList, currentBotObjectId!)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isMutiDialogOpen, setIsMutiDialogOpen] = useState(false)
  const [isInsertByUrlDialogOpen, setIsInsertByUrlDialogOpen] = useState(false)
  const [isInsertSingleDialogOpen, setIsInsertSingleDialogOpen] =
    useState(false)
  const [selected, setSelected] = useState<number[]>([])
  const [currentDeleteSearchItem, setCurrentDeleteSearchItem] =
    useState<SearchItem | null>(null)
  const [getSearchItems] = useLazyGetSearchItemsQuery()
  const [deleteSearchItems] = useDeleteSearchItemsMutation()
  const [insertSearchItem] = useInsertSearchItemMutation()
  const [insertSearchItemsByUrl] = useInsertSearchItemsByUrlMutation()

  const handleMutiDialogClose = () => {
    setIsMutiDialogOpen(false)
  }

  const handleMutiDialogConfirm = async () => {
    const deletedIdList = selected.map((index) => searchItems[index]?.object_id)

    await deleteSearchItems({
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

  const handleDialogConfirm = async () => {
    await deleteSearchItems({
      bot_class_id: botClassId,
      deleted_id_list: [currentDeleteSearchItem!.object_id!]
    }).then(() => {
      getSearchItems({ bot_class_id: botClassId })
    })
  }

  const handleAddSearchItemByUrl = () => {
    setIsInsertByUrlDialogOpen(true)
  }

  const handleInsertByUrlDialogClose = () => {
    setIsInsertByUrlDialogOpen(false)
  }

  const handleInsertByUrlDialogConfrim = async (data: { url: string }) => {
    await insertSearchItemsByUrl({
      bot_class_id: botClassId,
      url: data.url
    }).unwrap()
  }

  const handleAddSingleSearchItem = () => {
    setIsInsertSingleDialogOpen(true)
  }

  const handleInsertSingleDialogClose = () => {
    setIsInsertSingleDialogOpen(false)
  }

  const handleInsertSingleDialogConfirm = async (data: {
    item_name: string
    item_english_name: string
    item_type: string
    item_description: string
    item_price: string
    item_instruction: string
    item_ingredient: string
    item_url: string
  }) => {
    await insertSearchItem({
      bot_class_id: botClassId,
      ...data
    }).then(() => {
      getSearchItems({ bot_class_id: botClassId })
      handleInsertSingleDialogClose()
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
              className="search__button"
              variant="outlined"
              color="error"
              onClick={handleDelteItems}
              disabled={isEmpty(selected)}
            >
              {t(searchManagementPageContent.deleteButtonText)}
            </Button>
          )}
          <Button
            className="search__button"
            variant="outlined"
            onClick={handleAddSingleSearchItem}
          >
            {t(searchManagementPageContent.addButtonText)}
          </Button>
          <Button variant="outlined" onClick={handleAddSearchItemByUrl}>
            {t(searchManagementPageContent.addButtonTextByUrl)}
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
      {/* delete single search item dialog */}
      <CustomDialog
        isOpen={isDialogOpen}
        title={t(searchManagementPageContent.deleteDialogTitle, {
          item_name:
            currentDeleteSearchItem && currentDeleteSearchItem.chinese_name
        })}
        handleClose={handleDialogClose}
        onSubmit={handleDialogConfirm}
      />
      {/* delete muti selected search items dialog */}
      <CustomDialog
        isOpen={isMutiDialogOpen}
        handleClose={handleMutiDialogClose}
        title={t(searchManagementPageContent.deleteMutiDialogTitle)}
        onSubmit={handleMutiDialogConfirm}
      />
      {/* insert single search item dialog */}
      <CustomDialog<{
        item_name: string
        item_english_name: string
        item_type: string
        item_description: string
        item_price: string
        item_instruction: string
        item_ingredient: string
        item_url: string
      }>
        isOpen={isInsertSingleDialogOpen}
        handleClose={handleInsertSingleDialogClose}
        fields={insertSingleSearchItemFields}
        title={t(searchManagementPageContent.addButtonText)}
        onSubmit={async (data) => {
          await handleInsertSingleDialogConfirm(data)
        }}
      />
      {/* insert search items by url dialog */}
      <CustomDialog<{
        url: string
      }>
        isOpen={isInsertByUrlDialogOpen}
        handleClose={handleInsertByUrlDialogClose}
        fields={insertSearchItemsByUrlFields}
        title={searchManagementPageContent.insertByUrlDialogTitle}
        onSubmit={async (data) => {
          await handleInsertByUrlDialogConfrim(data)
        }}
      />
    </StyledSearchManagementPage>
  )
}
