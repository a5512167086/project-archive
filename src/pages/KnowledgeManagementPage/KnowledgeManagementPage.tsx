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
import { getBotClassId, isEmpty } from '@/utils/helper'
import { PAGE_PATHS } from '@/routes'
import { CustomDialog } from '@/components/CustomDialog'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'

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
  { id: 'question', label: '問題' },
  { id: 'answer', label: '回答' }
]

const insertSingleKnowledgeFields = [
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

const insertKnowledgesFields = [
  {
    id: 'csv_file',
    name: 'csv_file',
    label: 'knowledgeSettingPage.uploadCSV',
    type: 'file',
    required: true
  }
]

export const KnowledgeManagementPage = () => {
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
  const { knowledgeItems } = useAppSelector((state) => state.knowledge)
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const botClassId = getBotClassId(botList, currentBotObjectId!)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: knowledgeManagementPageContent.botPageTitle
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBotObjectId}`,
      linkText: currentBot!.bot_name
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
    await deleteKnowledges({
      bot_class_id: botClassId,
      deleted_id_list: [currentDeleteKnowledgeItem!.object_id!]
    }).then(() => {
      getKnowledges({ bot_class_id: botClassId })
    })
  }

  const handleDelteItems = () => {
    setIsMutiDialogOpen(true)
  }

  const handleMutiDialogClose = () => {
    setIsMutiDialogOpen(false)
  }

  const handleMutiDialogConfirm = async () => {
    const deletedIdList = selected.map(
      (index) => knowledgeItems[index]?.object_id
    )

    await deleteKnowledges({
      bot_class_id: botClassId,
      deleted_id_list: deletedIdList
    }).then(() => {
      setSelected([])
      getKnowledges({ bot_class_id: botClassId })
    })
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
    await insertKnowledge({
      bot_class_id: botClassId,
      ...data
    }).then(() => {
      getKnowledges({ bot_class_id: botClassId })
      handleInsertSingleDialogClose()
    })
  }

  const handleAddKnowledgesByCSV = () => {
    setIsInsertByCSVDialogOpen(true)
  }

  const handleInsertByCSVDialogClose = () => {
    setIsInsertByCSVDialogOpen(false)
  }

  const handleInsertByCSVDialogConfrim = async (data: { csv_file: File }) => {
    await insertKnowledges({
      bot_class_id: botClassId,
      csv_file: data.csv_file
    })
      .unwrap()
      .then(() => {
        getKnowledges({ bot_class_id: botClassId })
      })
  }

  useEffect(() => {
    getKnowledges({ bot_class_id: botClassId })
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
      {/* insert single knowledge dialog */}
      <CustomDialog<{
        question: string
        answer: string
      }>
        isOpen={isInsertSingleDialogOpen}
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
        isOpen={isInsertByCSVDialogOpen}
        handleClose={handleInsertByCSVDialogClose}
        fields={insertKnowledgesFields}
        title={knowledgeManagementPageContent.addButtonTextByCSV}
        onSubmit={async (data) => {
          await handleInsertByCSVDialogConfrim(data)
        }}
      />
      {/* delete single knowledge dialog */}
      <CustomDialog
        isOpen={isDialogOpen}
        title={t(knowledgeManagementPageContent.deleteDialogTitle, {
          knowledge_name:
            currentDeleteKnowledgeItem && currentDeleteKnowledgeItem.question
        })}
        handleClose={handleDialogClose}
        onSubmit={handleDialogConfirm}
      />
      {/* delete muti selected knowledges dialog */}
      <CustomDialog
        isOpen={isMutiDialogOpen}
        handleClose={handleMutiDialogClose}
        title={t(knowledgeManagementPageContent.deleteMutiDialogTitle)}
        onSubmit={handleMutiDialogConfirm}
      />
    </StyledKnowledgeManagementPage>
  )
}
