import { useEffect, useState } from 'react'
import { useAppSelector } from '@/utils/hook'
import { useTranslation } from 'react-i18next'
import {
  useCreateCategoryMutation,
  useUpdateCategoryMutation,
  useDeleteCategoryMutation,
  Category,
  useLazyGetCategoriesQuery
} from '@/store/apis/categoryApi'
import {
  Box,
  Button,
  Typography,
  IconButton,
  Card,
  CardHeader,
  CardContent,
  Collapse
} from '@mui/material'
import { Add, Edit, Delete } from '@mui/icons-material'
import { CustomDialog } from '@/components/CustomDialog'
import { isEmpty } from '@/utils/helper'
import { showSuccessToast } from '@/utils/toast'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'

export const CategoryManagement = () => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const { categoryList } = useAppSelector((state) => state.category)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [getCategories] = useLazyGetCategoriesQuery()
  const [createCategory] = useCreateCategoryMutation()
  const [updateCategory] = useUpdateCategoryMutation()
  const [deleteCategory] = useDeleteCategoryMutation()

  // Dialog states
  const [isInsertDialogOpen, setIsInsertDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [currentDeleteCategory, setCurrentDeleteCategory] =
    useState<Category | null>(null)
  const [parentCategoryId, setParentCategoryId] = useState<number | null>(null)

  useEffect(() => {
    if (currentBot?.bot_detail_id) {
      getCategories(currentBot.bot_detail_id)
    }
  }, [currentBot?.bot_detail_id, getCategories])

  // Dialog field definitions
  const createCategoryFields: FieldProps[] = [
    {
      id: 'category_name',
      name: 'category_name',
      label: t('productManagementPage.categoryName'),
      type: 'text',
      required: true,
      defaultValue: ''
    },
    {
      id: 'category_description',
      name: 'category_description',
      label: t('productManagementPage.categoryDescription'),
      type: 'text',
      required: false,
      defaultValue: ''
    }
  ]

  // 編輯 Dialog 欄位 (多一個 parent select)
  const editCategoryFields: FieldProps[] = [
    {
      id: 'category_name',
      name: 'category_name',
      label: t('productManagementPage.categoryName'),
      type: 'text',
      required: true,
      defaultValue: editingCategory?.category_name ?? ''
    },
    {
      id: 'category_description',
      name: 'category_description',
      label: t('productManagementPage.categoryDescription'),
      type: 'text',
      required: false,
      defaultValue: editingCategory?.category_description ?? ''
    },
    {
      id: 'parent_category_id',
      name: 'parent_category_id',
      label: t('productManagementPage.parentCategory'),
      type: 'select',
      required: false,
      options: [
        { label: t('productManagementPage.noParentCategory'), value: '0' },
        ...categoryList
          .filter((cat) => cat.class_id !== editingCategory?.class_id)
          .map((cat) => ({
            label: cat.category_name,
            value: String(cat.class_id)
          }))
      ],
      defaultValue:
        editingCategory?.parent_class_id === null ||
        editingCategory?.parent_class_id === undefined
          ? '0'
          : String(editingCategory?.parent_class_id)
    }
  ]

  // Handlers
  const handleOpenCreate = (parentId: number | null = null) => {
    setParentCategoryId(parentId)
    setEditingCategory(null)
    setIsInsertDialogOpen(true)
  }
  const handleCloseCreate = () => {
    setIsInsertDialogOpen(false)
    setParentCategoryId(null)
  }
  const handleOpenEdit = (cat: Category) => {
    setEditingCategory(cat)
    setIsEditDialogOpen(true)
  }
  const handleCloseEdit = () => {
    setIsEditDialogOpen(false)
    setEditingCategory(null)
  }
  const handleOpenDelete = (cat: Category) => {
    setCurrentDeleteCategory(cat)
    setIsDeleteDialogOpen(true)
  }
  const handleCloseDelete = () => {
    setIsDeleteDialogOpen(false)
    setTimeout(() => setCurrentDeleteCategory(null), 200)
  }

  // Confirm actions
  const handleInsertCategoryConfirm = async (data: {
    category_name: string
    category_description: string
  }) => {
    await createCategory({
      bot_uuid: currentBot!.bot_detail_id,
      category_name: data.category_name,
      category_description: data.category_description,
      parent_category_id: parentCategoryId ?? undefined
    }).unwrap()
    showSuccessToast(t('success.category_added'))
    getCategories(currentBot!.bot_detail_id)
    handleCloseCreate()
  }

  const handleEditCategoryConfirm = async (data: {
    category_name: string
    category_description: string
    parent_category_id?: string | number
  }) => {
    if (!editingCategory) return
    await updateCategory({
      bot_uuid: currentBot!.bot_detail_id,
      class_id: editingCategory.class_id,
      category_name: data.category_name,
      category_description: data.category_description,
      parent_category_id:
        data.parent_category_id === '0' ? 0 : Number(data.parent_category_id)
    }).unwrap()
    showSuccessToast(t('success.category_updated'))
    getCategories(currentBot!.bot_detail_id)
    handleCloseEdit()
  }

  const handleDeleteCategoryConfirm = async () => {
    if (!currentDeleteCategory) return
    await deleteCategory({
      bot_uuid: currentBot!.bot_detail_id,
      deleted_class_id_list: [currentDeleteCategory.class_id]
    }).unwrap()
    showSuccessToast(t('success.category_deleted'))
    getCategories(currentBot!.bot_detail_id)
    handleCloseDelete()
  }

  // Collapse state for each category
  const [collapseState, setCollapseState] = useState<{
    [key: number]: boolean
  }>({})

  const handleToggleCollapse = (classId: number) => {
    setCollapseState((prev) => ({ ...prev, [classId]: !prev[classId] }))
  }

  // Render category tree with actions
  const renderCategoryTreeWithActions = (categories: Category[], level = 0) => {
    return categories.map((cat) => {
      const hasChildren = cat.children && cat.children.length > 0
      const isCollapsed = collapseState[cat.class_id] ?? false
      return (
        <Box
          key={cat.class_id}
          sx={{
            pl: level * 3,
            pt: 1,
            borderLeft: level ? '1px solid #eee' : undefined,
            borderRadius: 1
          }}
        >
          <Box display="flex" alignItems="center" gap={1}>
            {/* Collapse Icon */}
            {hasChildren && (
              <IconButton
                size="small"
                onClick={() => handleToggleCollapse(cat.class_id)}
              >
                <span
                  style={{
                    display: 'inline-block',
                    transform: isCollapsed ? 'rotate(90deg)' : 'rotate(0deg)'
                  }}
                >
                  ▶
                </span>
              </IconButton>
            )}
            {/* Category name & description in one line */}
            <Box
              sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 2 }}
            >
              <Typography fontWeight={level === 0 ? 600 : 400}>
                {cat.category_name}
              </Typography>
              {cat.category_description && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ opacity: 0.7 }}
                >
                  {cat.category_description}
                </Typography>
              )}
            </Box>
            {/* Sub category count */}
            {hasChildren && (
              <Typography
                variant="caption"
                color="primary"
                sx={{ minWidth: 60 }}
              >
                ({cat.children.length})
              </Typography>
            )}
            <IconButton size="small" onClick={() => handleOpenEdit(cat)}>
              <Edit fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              color="error"
              onClick={() => handleOpenDelete(cat)}
            >
              <Delete fontSize="small" />
            </IconButton>
            <Button
              size="small"
              variant="outlined"
              startIcon={<Add />}
              onClick={() => handleOpenCreate(cat.class_id)}
            >
              {t('productManagementPage.addSubCategory')}
            </Button>
          </Box>
          {/* Children collapse */}
          {hasChildren && (
            <Collapse in={isCollapsed} timeout="auto" unmountOnExit>
              <Box sx={{ ml: 2 }}>
                {renderCategoryTreeWithActions(cat.children, level + 1)}
              </Box>
            </Collapse>
          )}
        </Box>
      )
    })
  }

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0
      }}
    >
      <Card
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
          overflow: 'hidden'
        }}
      >
        <CardHeader
          title={t('productManagementPage.categoryManagement')}
          sx={{ flexShrink: 0 }}
          action={
            <Box display="flex">
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => handleOpenCreate(null)}
              >
                {t('productManagementPage.addCategory')}
              </Button>
            </Box>
          }
        />
        <CardContent
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            padding: 2,
            '&:last-child': {
              paddingBottom: 2
            }
          }}
        >
          {isEmpty(categoryList) ? (
            <Typography color="text.secondary" align="center" sx={{ mt: 4 }}>
              {t('productManagementPage.noCategory')}
            </Typography>
          ) : (
            renderCategoryTreeWithActions(categoryList)
          )}
          {/* 新增分類 Dialog */}
          <CustomDialog
            open={isInsertDialogOpen}
            handleClose={handleCloseCreate}
            title={t('productManagementPage.addCategory')}
            fields={createCategoryFields}
            maxWidth="sm"
            onSubmit={handleInsertCategoryConfirm}
            dangerButton={false}
          />
          {/* 編輯分類 Dialog */}
          {editingCategory && (
            <CustomDialog
              open={isEditDialogOpen}
              handleClose={handleCloseEdit}
              title={t('productManagementPage.editCategory')}
              fields={editCategoryFields}
              maxWidth="sm"
              onSubmit={handleEditCategoryConfirm}
              dangerButton={false}
            />
          )}
          {/* 刪除分類 Dialog */}
          <CustomDialog
            open={isDeleteDialogOpen}
            title={t('productManagementPage.deleteCategorySingleTitle', {
              name: currentDeleteCategory?.category_name
            })}
            handleClose={handleCloseDelete}
            onSubmit={handleDeleteCategoryConfirm}
          />
        </CardContent>
      </Card>
    </Box>
  )
}
