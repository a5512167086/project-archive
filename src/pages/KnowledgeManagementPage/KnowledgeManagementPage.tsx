import { Box, Button, Typography } from '@mui/material'
import { StyledKnowledgeManagementPage } from './KnowledgeManagementPage.style'
import { useTranslation } from 'react-i18next'
import { CustomTable } from '@/components/CustomTable'
import {
  KnowledgeItem,
  useDeleteKnowledgeItemsMutation,
  useInsertKnowledgeItemMutation,
  useInsertKnowledgeItemsByCSVMutation,
  useLazyGetKnowledgeItemsQuery
} from '@/store/apis/knowledgeApi'
import { useEffect, useState } from 'react'
import { useAppSelector } from '@/utils/hook'
import { isEmpty } from '@/utils/helper'
import { PAGE_PATHS } from '@/routes'
import { CustomDialog } from '@/components/CustomDialog'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { useApiHandler } from '@/hooks/useApiHandler'

const knowledgeManagementPageContent = {
  title: 'knowledgeSettingPage.title',
  addButtonText: 'knowledgeSettingPage.addKnowledgeItemButton',
  addButtonTextByCSV: 'knowledgeSettingPage.addKnowledgeItemFromCSVButton',
  deleteButtonText: 'knowledgeSettingPage.deleteSelectedKnowledgeItems',
  deleteDialogTitle: 'knowledgeSettingPage.deleteKnowledgeItemTitle',
  deleteMutiDialogTitle: 'knowledgeSettingPage.deleteKnowledgeItemsTitle',
  botPageTitle: 'botPage.myBot'
}

const columns = [
  { id: 'question', label: 'knowledgeSettingPage.question' },
  { id: 'answer', label: 'knowledgeSettingPage.answer' }
]

const insertSingleKnowledgeFields: FieldProps[] = [
  {
    id: 'question',
    name: 'question',
    label: 'knowledgeSettingPage.question',
    type: 'text',
    required: true
  },
  {
    id: 'answer',
    name: 'answer',
    label: 'knowledgeSettingPage.answer',
    type: 'text',
    required: true
  }
]

const insertKnowledgesFields: FieldProps[] = [
  {
    id: 'csv_file',
    name: 'csv_file',
    label: 'knowledgeSettingPage.uploadCSV',
    type: 'file',
    required: true,
    errorText: {
      invalidFormat: 'Please upload a valid CSV file'
    }
  }
]

const KnowledgeManagementPage = () => {
  const [getKnowledges] = useLazyGetKnowledgeItemsQuery()
  const [insertKnowledge] = useInsertKnowledgeItemMutation()
  const [insertKnowledges] = useInsertKnowledgeItemsByCSVMutation()
  const [deleteKnowledges] = useDeleteKnowledgeItemsMutation()
  const [selected, setSelected] = useState<number[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isMutiDialogOpen, setIsMutiDialogOpen] = useState(false)
  const [isInsertSingleDialogOpen, setIsInsertSingleDialogOpen] =
    useState(false)
  const [isInsertByCSVDialogOpen, setIsInsertByCSVDialogOpen] = useState(false)
  const [currentDeleteKnowledgeItem, setCurrentDeleteKnowledgeItem] =
    useState<KnowledgeItem | null>(null)
  const { t } = useTranslation()
  const { handleError, showSuccess } = useApiHandler()
  const { knowledgeItems } = useAppSelector((state) => state.knowledge)
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: knowledgeManagementPageContent.botPageTitle
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBotObjectId}`,
      linkText: currentBot!.chinese_name
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBotObjectId}/${PAGE_PATHS.KNOWLEDGE_MOUDLE}`,
      linkText: knowledgeManagementPageContent.title
    }
  ]

  const handleDeleteItem = (item: KnowledgeItem) => {
    setCurrentDeleteKnowledgeItem(item)
    setIsDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDialogOpen(false)
    // Delay clear currentDeleteKnowledgeItem to prevent item name flickering
    setTimeout(() => {
      setCurrentDeleteKnowledgeItem(null)
    }, 100)
  }

  const handleDialogConfirm = async () => {
    try {
      await deleteKnowledges({
        bot_uuid: currentBot!.bot_detail_id,
        deleted_id_list: [currentDeleteKnowledgeItem!.object_id!]
      }).unwrap()

      showSuccess('success.knowledge_deleted')
      getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
    } catch (error) {
      handleError(error)
    }
  }

  const handleDelteItems = () => {
    setIsMutiDialogOpen(true)
  }

  const handleMutiDialogClose = () => {
    setIsMutiDialogOpen(false)
  }

  const handleMutiDialogConfirm = async () => {
    try {
      const deletedIdList = selected.map(
        (index) => knowledgeItems[index]?.object_id
      )

      await deleteKnowledges({
        bot_uuid: currentBot!.bot_detail_id,
        deleted_id_list: deletedIdList
      }).unwrap()

      showSuccess('success.knowledges_deleted')
      setSelected([])
      getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
    } catch (error) {
      handleError(error)
    }
  }

  const handleAddSingleKnowledge = () => {
    setIsInsertSingleDialogOpen(true)
  }

  const handleInsertSingleDialogClose = () => {
    setIsInsertSingleDialogOpen(false)
  }

  const handleInsertSingleDialogConfirm = async (data: {
    question: string
    answer: string
  }) => {
    try {
      await insertKnowledge({
        bot_uuid: currentBot!.bot_detail_id,
        ...data
      }).unwrap()

      showSuccess('success.knowledge_added')
      getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
      handleInsertSingleDialogClose()
    } catch (error) {
      handleError(error)
    }
  }

  const handleAddKnowledgesByCSV = () => {
    setIsInsertByCSVDialogOpen(true)
  }

  const handleInsertByCSVDialogClose = () => {
    setIsInsertByCSVDialogOpen(false)
  }

  const handleInsertByCSVDialogConfirm = async (data: { csv_file: File }) => {
    // Validate CSV file type
    if (
      !data.csv_file.type.includes('csv') &&
      !data.csv_file.name.toLowerCase().endsWith('.csv')
    ) {
      handleError(null, t('error.invalid_file_type'))
      return
    }

    try {
      await insertKnowledges({
        bot_uuid: currentBot!.bot_detail_id,
        csv_file: data.csv_file
      }).unwrap()

      showSuccess('success.csv_imported')
      getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
    } catch (error) {
      handleError(error)
    }
  }

  useEffect(() => {
    getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
  }, [])

  return (
    <StyledKnowledgeManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box className="knowledge__titleBox">
        <Typography variant="h5" className="knowledge__title">
          {t(knowledgeManagementPageContent.title)}
        </Typography>
        <Box>
          {!isEmpty(selected) && (
            <Button
              className="knowledge__button"
              variant="outlined"
              color="error"
              onClick={handleDelteItems}
            >
              {t(knowledgeManagementPageContent.deleteButtonText)}
            </Button>
          )}
          <Button
            className="knowledge__button"
            variant="outlined"
            onClick={handleAddSingleKnowledge}
          >
            {t(knowledgeManagementPageContent.addButtonText)}
          </Button>
          <Button variant="outlined" onClick={handleAddKnowledgesByCSV}>
            {t(knowledgeManagementPageContent.addButtonTextByCSV)}
          </Button>
        </Box>
      </Box>
      <div className="knowledge__tableContainer">
        <CustomTable
          data={knowledgeItems}
          columns={columns}
          selected={selected}
          setSelected={setSelected}
          onEdit={() => {}}
          onDelete={(item) => {
            handleDeleteItem(item)
          }}
        />
      </div>
      {/* insert single knowledge dialog */}
      <CustomDialog<{
        question: string
        answer: string
      }>
        open={isInsertSingleDialogOpen}
        handleClose={handleInsertSingleDialogClose}
        fields={insertSingleKnowledgeFields}
        title={t(knowledgeManagementPageContent.addButtonText)}
        onSubmit={async (data) => {
          await handleInsertSingleDialogConfirm(data)
        }}
      />
      {/* insert knowledges by csv dialog */}
      <CustomDialog<{
        csv_file: File
      }>
        open={isInsertByCSVDialogOpen}
        handleClose={handleInsertByCSVDialogClose}
        fields={insertKnowledgesFields}
        title={knowledgeManagementPageContent.addButtonTextByCSV}
        onSubmit={async (data) => {
          await handleInsertByCSVDialogConfirm(data)
        }}
      />
      {/* delete single knowledge dialog */}
      <CustomDialog
        open={isDialogOpen}
        title={t(knowledgeManagementPageContent.deleteDialogTitle, {
          knowledge_name:
            currentDeleteKnowledgeItem && currentDeleteKnowledgeItem.question
        })}
        handleClose={handleDialogClose}
        onSubmit={handleDialogConfirm}
      />
      {/* delete muti selected knowledges dialog */}
      <CustomDialog
        open={isMutiDialogOpen}
        handleClose={handleMutiDialogClose}
        title={t(knowledgeManagementPageContent.deleteMutiDialogTitle)}
        onSubmit={handleMutiDialogConfirm}
      />
    </StyledKnowledgeManagementPage>
  )
}

export default KnowledgeManagementPage
