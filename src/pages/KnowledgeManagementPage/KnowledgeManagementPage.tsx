import { Box, Button, Typography } from '@mui/material'
import { StyledKnowledgeManagementPage } from './KnowledgeManagementPage.style'
import { useTranslation } from 'react-i18next'
import { CustomTable } from '@/components/CustomTable'
import {
  KnowledgeItem,
  useDeleteKnowledgeItemsMutation,
  useInsertKnowledgeItemMutation,
  useInsertKnowledgeItemsByCSVMutation,
  useLazyGetKnowledgeItemsQuery,
  useUpdateKnowledgeItemMutation
} from '@/store/apis/knowledgeApi'
import { useEffect, useState } from 'react'
import { useAppSelector } from '@/utils/hook'
import { isEmpty } from '@/utils/helper'
import { PAGE_PATHS } from '@/routes'
import { CustomDialog } from '@/components/CustomDialog'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { useParams } from 'react-router-dom'

const knowledgeManagementPageContent = {
  title: 'knowledgeSettingPage.title',
  addButtonText: 'knowledgeSettingPage.addKnowledgeItemButton',
  syncButtonText: 'knowledgeSettingPage.syncKnowledgeItemsButton',
  editButtonText: 'knowledgeSettingPage.editKnowledgeItemButton',
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

const knowledgeFormFields: FieldProps[] = [
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
  const { uuid } = useParams()
  const [getKnowledges] = useLazyGetKnowledgeItemsQuery()
  const [insertKnowledge] = useInsertKnowledgeItemMutation()
  const [updateKnowledge] = useUpdateKnowledgeItemMutation()
  const [insertKnowledges] = useInsertKnowledgeItemsByCSVMutation()
  const [deleteKnowledges] = useDeleteKnowledgeItemsMutation()
  const [selected, setSelected] = useState<number[]>([])
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isMutiDeleteDialogOpen, setIsMutiDeleteDialogOpen] = useState(false)
  const [isInsertSingleDialogOpen, setIsInsertSingleDialogOpen] =
    useState(false)
  const [isInsertByCSVDialogOpen, setIsInsertByCSVDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [currentDeleteKnowledgeItem, setCurrentDeleteKnowledgeItem] =
    useState<KnowledgeItem | null>(null)
  const [editingKnowledgeItem, setEditingKnowledgeItem] =
    useState<KnowledgeItem | null>(null)
  const { t } = useTranslation()
  const { knowledgeItems } = useAppSelector((state) => state.knowledge)
  const { botList } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.bot_detail_id === uuid)
  const breadcrumbItems = [
    {
      link: PAGE_PATHS.BOT_LIST,
      linkText: knowledgeManagementPageContent.botPageTitle
    },
    {
      link: PAGE_PATHS.BOT_LIST + `/${currentBot?.bot_detail_id}`,
      linkText: currentBot!.chinese_name
    },
    {
      link: `${PAGE_PATHS.BOT_LIST}/${currentBot?.bot_detail_id}/${PAGE_PATHS.KNOWLEDGE_MOUDLE}`,
      linkText: knowledgeManagementPageContent.title
    }
  ]

  const handleDeleteItem = (item: KnowledgeItem) => {
    setCurrentDeleteKnowledgeItem(item)
    setIsDeleteDialogOpen(true)
  }

  const handleDialogClose = () => {
    setIsDeleteDialogOpen(false)
    setTimeout(() => {
      setCurrentDeleteKnowledgeItem(null)
    }, 200)
  }

  const handleDialogConfirm = async () => {
    await deleteKnowledges({
      bot_uuid: currentBot!.bot_detail_id,
      deleted_id_list: [currentDeleteKnowledgeItem!.object_id!]
    }).unwrap()

    showSuccessToast('success.knowledge_deleted', t)
    getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
  }

  const handleDelteItems = () => {
    setIsMutiDeleteDialogOpen(true)
  }

  const handleMutiDialogClose = () => {
    setIsMutiDeleteDialogOpen(false)
  }

  const handleMutiDialogConfirm = async () => {
    const deletedIdList = selected.map(
      (index) => knowledgeItems[index]?.object_id
    )

    await deleteKnowledges({
      bot_uuid: currentBot!.bot_detail_id,
      deleted_id_list: deletedIdList
    }).unwrap()

    showSuccessToast('success.knowledges_deleted', t)
    setSelected([])
    getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
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
      bot_uuid: currentBot!.bot_detail_id,
      ...data
    }).unwrap()

    showSuccessToast('success.knowledge_added', t)
    getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
    handleInsertSingleDialogClose()
  }

  const handleAddKnowledgesByCSV = () => {
    setIsInsertByCSVDialogOpen(true)
  }

  const handleInsertByCSVDialogClose = () => {
    setIsInsertByCSVDialogOpen(false)
  }

  const handleInsertByCSVDialogConfirm = async (data: { csv_file: File }) => {
    if (
      !data.csv_file.type.includes('csv') &&
      !data.csv_file.name.toLowerCase().endsWith('.csv')
    ) {
      showErrorToast(null, t, 'error.invalid_file_type')
      return
    }

    await insertKnowledges({
      bot_uuid: currentBot!.bot_detail_id,
      csv_file: data.csv_file
    }).unwrap()

    showSuccessToast('success.csv_imported', t)
    getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
  }

  const handleEditItem = (item: KnowledgeItem) => {
    setEditingKnowledgeItem(item)
    setIsEditDialogOpen(true)
  }

  const handleEditDialogClose = () => {
    setIsEditDialogOpen(false)
    setEditingKnowledgeItem(null)
  }

  const handleEditDialogConfirm = async (data: {
    question: string
    answer: string
  }) => {
    if (!editingKnowledgeItem) return

    await updateKnowledge({
      bot_uuid: currentBot!.bot_detail_id,
      object_id: editingKnowledgeItem.object_id,
      ...data
    }).unwrap()

    showSuccessToast('success.knowledge_updated', t)
    getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
    handleEditDialogClose()
  }

  useEffect(() => {
    getKnowledges({ bot_uuid: currentBot!.bot_detail_id })
  }, [])

  return (
    <StyledKnowledgeManagementPage disableGutters maxWidth={false}>
      <CustomBreadcrumb items={breadcrumbItems} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexShrink: 0,
          marginBottom: '16px'
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontSize: '2rem',
            fontWeight: '500'
          }}
        >
          {t(knowledgeManagementPageContent.title)}
        </Typography>
        <Box>
          {!isEmpty(selected) && (
            <Button
              variant="outlined"
              color="error"
              onClick={handleDelteItems}
              sx={{ marginRight: '10px' }}
            >
              {t(knowledgeManagementPageContent.deleteButtonText)}
            </Button>
          )}
          <Button variant="outlined" sx={{ marginRight: '10px' }}>
            {t(knowledgeManagementPageContent.syncButtonText)}
          </Button>
          <Button
            variant="outlined"
            onClick={handleAddSingleKnowledge}
            sx={{ marginRight: '10px' }}
          >
            {t(knowledgeManagementPageContent.addButtonText)}
          </Button>
          <Button variant="outlined" onClick={handleAddKnowledgesByCSV}>
            {t(knowledgeManagementPageContent.addButtonTextByCSV)}
          </Button>
        </Box>
      </Box>
      <Box className="knowledge__tableContainer">
        <CustomTable
          data={knowledgeItems}
          columns={columns}
          selected={selected}
          setSelected={setSelected}
          onEdit={handleEditItem}
          onDelete={handleDeleteItem}
        />
      </Box>
      <CustomDialog<{
        question: string
        answer: string
      }>
        open={isInsertSingleDialogOpen}
        handleClose={handleInsertSingleDialogClose}
        fields={knowledgeFormFields}
        title={t(knowledgeManagementPageContent.addButtonText)}
        onSubmit={handleInsertSingleDialogConfirm}
      />
      {editingKnowledgeItem && (
        <CustomDialog<{
          question: string
          answer: string
        }>
          open={isEditDialogOpen}
          handleClose={handleEditDialogClose}
          fields={knowledgeFormFields.map((field) => ({
            ...field,
            defaultValue:
              editingKnowledgeItem[field.name as keyof KnowledgeItem]
          }))}
          title={t(knowledgeManagementPageContent.editButtonText)}
          onSubmit={handleEditDialogConfirm}
        />
      )}
      <CustomDialog<{
        csv_file: File
      }>
        open={isInsertByCSVDialogOpen}
        handleClose={handleInsertByCSVDialogClose}
        fields={insertKnowledgesFields}
        title={knowledgeManagementPageContent.addButtonTextByCSV}
        onSubmit={handleInsertByCSVDialogConfirm}
      />
      <CustomDialog
        open={isDeleteDialogOpen}
        title={t(knowledgeManagementPageContent.deleteDialogTitle, {
          knowledge_name:
            currentDeleteKnowledgeItem && currentDeleteKnowledgeItem.question
        })}
        handleClose={handleDialogClose}
        onSubmit={handleDialogConfirm}
      />
      <CustomDialog
        open={isMutiDeleteDialogOpen}
        handleClose={handleMutiDialogClose}
        title={t(knowledgeManagementPageContent.deleteMutiDialogTitle)}
        onSubmit={handleMutiDialogConfirm}
      />
    </StyledKnowledgeManagementPage>
  )
}

export default KnowledgeManagementPage
