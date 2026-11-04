import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Tabs,
  Tab
} from '@mui/material'
import SyncIcon from '@mui/icons-material/Sync'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import FileUploadIcon from '@mui/icons-material/FileUpload'
import { useAppSelector } from '@/utils/hook'
import { CustomTable } from '@/components/CustomTable'
import { CustomDialog } from '@/components/CustomDialog'
import { CustomBreadcrumb } from '@/components/CustomBreadcrumb'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import {
  useLazyGetKnowledgeItemsQuery,
  useInsertKnowledgeItemMutation,
  useInsertKnowledgeItemsByCSVMutation,
  useUpdateKnowledgeItemMutation,
  useDeleteKnowledgeItemsMutation,
  useLazyGetKnowledgeFilesQuery,
  useInsertKnowledgeFilesMutation,
  useDeleteKnowledgeFilesMutation,
  useUpdateKnowledgeFileMutation,
  useLazyDownloadKnowledgeFileQuery,
  useGetSyncStatusQuery,
  useTriggerSyncMutation,
  KnowledgeFileItem,
  KnowledgeItem
} from '@/store/apis/knowledgeApi'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { StyledKnowledgeManagementPage } from './KnowledgeManagementPage.style'

const KnowledgeManagementPage = () => {
  const { uuid } = useParams()
  const { t } = useTranslation()
  const [tabValue, setTabValue] = useState(0)

  const { knowledgeItems, knowledgeFiles } = useAppSelector(
    (state) => state.knowledge
  )
  const { botList } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.bot_detail_id === uuid)

  const [pollingInterval, setPollingInterval] = useState(0)

  const [getKnowledges] = useLazyGetKnowledgeItemsQuery()
  const [insertQA] = useInsertKnowledgeItemMutation()
  const [insertQAByCSV] = useInsertKnowledgeItemsByCSVMutation()
  const [updateQA] = useUpdateKnowledgeItemMutation()
  const [deleteQA] = useDeleteKnowledgeItemsMutation()
  const [getFiles] = useLazyGetKnowledgeFilesQuery()
  const [insertFiles] = useInsertKnowledgeFilesMutation()
  const [updateFile] = useUpdateKnowledgeFileMutation()
  const [deleteFiles] = useDeleteKnowledgeFilesMutation()
  const [triggerDownload] = useLazyDownloadKnowledgeFileQuery()
  const [triggerSync, { isLoading: isSyncing }] = useTriggerSyncMutation()
  const { data: syncStatus } = useGetSyncStatusQuery(
    { bot_uuid: uuid! },
    {
      skip: !uuid,
      pollingInterval: pollingInterval
    }
  )

  useEffect(() => {
    if (syncStatus?.status === 'RUNNING') {
      setPollingInterval(5000)
    } else {
      setPollingInterval(0)
    }
  }, [syncStatus?.status])

  const [selectedQA, setSelectedQA] = useState<number[]>([])
  const [selectedFiles, setSelectedFiles] = useState<number[]>([])
  const [isAddQAOpen, setIsAddQAOpen] = useState(false)
  const [isAddCSVOpen, setIsAddCSVOpen] = useState(false)
  const [editingQA, setEditingQA] = useState<KnowledgeItem | null>(null)
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [editingFile, setEditingFile] = useState<KnowledgeFileItem | null>(null)
  const [isDeleteQAOpen, setIsDeleteQAOpen] = useState(false)
  const [isDeleteFilesOpen, setIsDeleteFilesOpen] = useState(false)

  const isSyncRunning = isSyncing || syncStatus?.status === 'RUNNING'

  const canSync =
    syncStatus?.status === 'PENDING' ||
    syncStatus?.status === 'FAILED' ||
    syncStatus?.has_pending_changes

  const getSyncText = () => {
    if (isSyncRunning) return t('knowledgeSettingPage.syncing')
    if (!canSync && syncStatus?.status === 'COMPLETED')
      return t('knowledgeSettingPage.syncCompleted')
    return t('knowledgeSettingPage.sync')
  }

  useEffect(() => {
    if (uuid) {
      if (tabValue === 0) {
        getKnowledges({ bot_uuid: uuid })
      } else {
        getFiles({ bot_uuid: uuid })
      }
    }
  }, [tabValue, uuid, getKnowledges, getFiles])

  // ... (這裡保留你原本的 handlers：handleAddQAConfirm, handleAddCSVConfirm, 等等) ...
  const handleAddQAConfirm = async (data: {
    question: string
    answer: string
  }) => {
    try {
      await insertQA({ bot_uuid: uuid!, ...data }).unwrap()
      showSuccessToast('success.add', t)
      setIsAddQAOpen(false)
      getKnowledges({ bot_uuid: uuid! })
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const handleAddCSVConfirm = async (data: { csv_file: File }) => {
    try {
      if (!data.csv_file || !data.csv_file.name.endsWith('.csv')) {
        showErrorToast('error.invalid_file_type', t)
        return
      }
      await insertQAByCSV({ bot_uuid: uuid!, csv_file: data.csv_file }).unwrap()
      showSuccessToast('success.upload', t)
      getKnowledges({ bot_uuid: uuid! })
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const handleEditQAConfirm = async (data: {
    question: string
    answer: string
  }) => {
    if (!editingQA) return
    try {
      await updateQA({
        bot_uuid: uuid!,
        object_id: editingQA.object_id,
        ...data
      }).unwrap()
      showSuccessToast('success.update', t)
      setEditingQA(null)
      getKnowledges({ bot_uuid: uuid! })
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const handleConfirmDeleteQA = async () => {
    const ids = selectedQA.map((idx) => knowledgeItems[idx].object_id)
    try {
      await deleteQA({ bot_uuid: uuid!, deleted_id_list: ids }).unwrap()
      setSelectedQA([])
      showSuccessToast('success.delete', t)
      setIsDeleteQAOpen(false)
      getKnowledges({ bot_uuid: uuid! })
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const handleDownload = async (file: KnowledgeFileItem) => {
    try {
      const blob = await triggerDownload({
        bot_uuid: uuid!,
        file_id: file.file_id
      }).unwrap()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const handleUploadConfirm = async (data: { files: File[] }) => {
    try {
      const fileArray = Array.isArray(data.files) ? data.files : [data.files]
      if (fileArray.length === 0) return

      await insertFiles({ bot_uuid: uuid!, files: fileArray }).unwrap()
      showSuccessToast('success.upload', t)
      setIsUploadOpen(false)
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const handleEditFileConfirm = async (data: { display_name: string }) => {
    if (!editingFile) return
    try {
      await updateFile({
        bot_uuid: uuid!,
        file_id: editingFile.file_id,
        display_name: data.display_name
      }).unwrap()
      showSuccessToast('success.update', t)
      setEditingFile(null)
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const handleConfirmDeleteFiles = async () => {
    const ids = selectedFiles.map((idx) => knowledgeFiles[idx].file_id)
    try {
      await deleteFiles({ bot_uuid: uuid!, file_id_list: ids }).unwrap()
      setSelectedFiles([])
      showSuccessToast('success.delete', t)
      setIsDeleteFilesOpen(false)
    } catch (e) {
      showErrorToast(e, t)
    }
  }

  const addQAFields: FieldProps[] = [
    {
      id: 'question',
      name: 'question',
      type: 'text',
      label: 'knowledgeSettingPage.question',
      required: true
    },
    {
      id: 'answer',
      name: 'answer',
      type: 'text',
      label: 'knowledgeSettingPage.answer',
      required: true
    }
  ]

  const csvFields: FieldProps[] = [
    {
      id: 'csv_file',
      name: 'csv_file',
      type: 'file',
      label: 'knowledgeSettingPage.uploadCSV',
      required: true,
      accept: '.csv'
    }
  ]

  const uploadFields: FieldProps[] = [
    {
      id: 'files',
      name: 'files',
      type: 'file',
      label: 'knowledgeSettingPage.uploadFile',
      required: true,
      multiple: true
    }
  ]

  const editFileFields: FieldProps[] = [
    {
      id: 'display_name',
      name: 'display_name',
      type: 'text',
      label: 'knowledgeSettingPage.fileName',
      required: true,
      defaultValue: editingFile?.display_name
    }
  ]

  const getEditQAFields = (): FieldProps[] => [
    {
      id: 'question',
      name: 'question',
      type: 'text',
      label: 'knowledgeSettingPage.question',
      required: true,
      defaultValue: editingQA?.question
    },
    {
      id: 'answer',
      name: 'answer',
      type: 'text',
      label: 'knowledgeSettingPage.answer',
      required: true,
      defaultValue: editingQA?.answer
    }
  ]

  return (
    <StyledKnowledgeManagementPage disableGutters maxWidth={false}>
      <Box sx={{ flexShrink: 0 }}>
        <CustomBreadcrumb
          items={[
            { linkText: t('botPage.myBot'), link: '/bot-list' },
            { linkText: currentBot?.chinese_name || '', link: `/bot-list/${uuid}` }
          ]}
        />
      </Box>

      <div className="knowledge__titleBox">
        <Typography className="knowledge__title" variant="h4">
          {t('knowledgeSettingPage.title')}
        </Typography>

        <Box>
          <Button
            className="knowledge__button"
            variant="outlined"
            startIcon={
              isSyncRunning ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <SyncIcon />
              )
            }
            onClick={() => triggerSync({ bot_uuid: uuid! })}
            disabled={!canSync || isSyncRunning}
          >
            {getSyncText()}
          </Button>

          {tabValue === 0 && (
            <>
              {selectedQA.length > 0 && (
                <Button
                  className="knowledge__button"
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setIsDeleteQAOpen(true)}
                >
                  {t('common.delete')} ({selectedQA.length})
                </Button>
              )}
              <Button
                className="knowledge__button"
                variant="outlined"
                startIcon={<FileUploadIcon />}
                onClick={() => setIsAddCSVOpen(true)}
              >
                {t('knowledgeSettingPage.importCSV')}
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setIsAddQAOpen(true)}
              >
                {t('knowledgeSettingPage.addSingle')}
              </Button>
            </>
          )}

          {tabValue === 1 && (
            <>
              {selectedFiles.length > 0 && (
                <Button
                  className="knowledge__button"
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setIsDeleteFilesOpen(true)}
                >
                  {t('common.delete')} ({selectedFiles.length})
                </Button>
              )}
              <Button variant="contained" onClick={() => setIsUploadOpen(true)}>
                {t('knowledgeSettingPage.uploadFile')}
              </Button>
            </>
          )}
        </Box>
      </div>

      <Tabs
        value={tabValue}
        onChange={(_, v) => setTabValue(v)}
        sx={{ mb: 2, flexShrink: 0 }}
      >
        <Tab label={t('knowledgeSettingPage.qaTab')} />
        <Tab label={t('knowledgeSettingPage.fileTab')} />
      </Tabs>

      <div className="knowledge__tableContainer">
        {tabValue === 0 && (
          <CustomTable
            data={knowledgeItems}
            columns={[
              { id: 'question', label: 'knowledgeSettingPage.question' },
              { id: 'answer', label: 'knowledgeSettingPage.answer' }
            ]}
            selected={selectedQA}
            setSelected={setSelectedQA}
            onEdit={(item: KnowledgeItem) => setEditingQA(item)}
          />
        )}
        {tabValue === 1 && (
          <CustomTable
            data={knowledgeFiles}
            columns={[
              { id: 'display_name', label: 'knowledgeSettingPage.fileName' },
              { id: 'file_type', label: 'knowledgeSettingPage.fileType' },
              { id: 'created_at', label: 'knowledgeSettingPage.createdAt' }
            ]}
            selected={selectedFiles}
            setSelected={setSelectedFiles}
            onEdit={(item: KnowledgeFileItem) => setEditingFile(item)}
            onDownload={(item: KnowledgeFileItem) => handleDownload(item)}
          />
        )}
      </div>

      <CustomDialog
        open={isAddQAOpen}
        title="knowledgeSettingPage.addSingle"
        fields={addQAFields}
        handleClose={() => setIsAddQAOpen(false)}
        onSubmit={handleAddQAConfirm}
      />
      <CustomDialog
        open={isAddCSVOpen}
        title="knowledgeSettingPage.importCSV"
        fields={csvFields}
        handleClose={() => setIsAddCSVOpen(false)}
        onSubmit={handleAddCSVConfirm}
      />
      {editingQA && (
        <CustomDialog
          open={!!editingQA}
          title="knowledgeSettingPage.editQA"
          fields={getEditQAFields()}
          handleClose={() => setEditingQA(null)}
          onSubmit={handleEditQAConfirm}
        />
      )}
      <CustomDialog
        open={isUploadOpen}
        title="knowledgeSettingPage.uploadFile"
        fields={uploadFields}
        handleClose={() => setIsUploadOpen(false)}
        onSubmit={handleUploadConfirm}
      />
      {editingFile && (
        <CustomDialog
          open={!!editingFile}
          title="knowledgeSettingPage.editFileName"
          fields={editFileFields}
          handleClose={() => setEditingFile(null)}
          onSubmit={handleEditFileConfirm}
        />
      )}
      <CustomDialog
        open={isDeleteQAOpen}
        title="knowledgeSettingPage.deleteKnowledgeItemsTitle"
        description="knowledgeSettingPage.deleteKnowledgeItemsTitle"
        fields={[]}
        dangerButton={true}
        handleClose={() => setIsDeleteQAOpen(false)}
        onSubmit={handleConfirmDeleteQA}
      />
      <CustomDialog
        open={isDeleteFilesOpen}
        title="knowledgeSettingPage.deleteKnowledgeItemsTitle"
        description="knowledgeSettingPage.deleteKnowledgeItemsTitle"
        fields={[]}
        dangerButton={true}
        handleClose={() => setIsDeleteFilesOpen(false)}
        onSubmit={handleConfirmDeleteFiles}
      />
    </StyledKnowledgeManagementPage>
  )
}

export default KnowledgeManagementPage
