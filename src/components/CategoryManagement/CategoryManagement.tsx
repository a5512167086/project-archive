import React from 'react'
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Grid,
  Collapse,
  List,
  ListItem,
  Typography,
  CircularProgress
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '@/utils/hook'
import {
  useCreateCategoryMutation,
  useUpdateCategoryMutation,
  useDeleteCategoryMutation,
  useLazyGetCategoriesQuery
} from '@/store/apis/categoryApi'
import { showSuccessToast } from '@/utils/toast'
import { CustomDialog } from '@/components/CustomDialog'

interface Category {
  id: string
  name: string
  description: string
  parentId?: string
  children?: Category[]
}

interface CategoryForm {
  name: string
  description: string
  parentId: string
}

interface CategoryManagementProps {
  categories: Category[]
  expandedCategories: string[]
  categoryDialog: boolean
  editingCategory: Category | null
  categoryForm: CategoryForm
  onExpandedCategoriesChange: (expanded: string[]) => void
  onCategoryDialogChange: (open: boolean) => void
  onEditingCategoryChange: (category: Category | null) => void
  onCategoryFormChange: (form: CategoryForm) => void
}

const CategoryManagement: React.FC<CategoryManagementProps> = ({
  categories,
  expandedCategories,
  categoryDialog,
  editingCategory,
  categoryForm,
  onExpandedCategoriesChange,
  onCategoryDialogChange,
  onEditingCategoryChange,
  onCategoryFormChange
}) => {
  const { t } = useTranslation()
  const { botList, currentBotObjectId } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.object_id === currentBotObjectId)
  const [getCategories] = useLazyGetCategoriesQuery()
  const [createCategory, { isLoading: isCreating }] =
    useCreateCategoryMutation()
  const [updateCategory, { isLoading: isUpdating }] =
    useUpdateCategoryMutation()
  const [deleteCategory] = useDeleteCategoryMutation()
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)
  const [currentDeleteCategory, setCurrentDeleteCategory] =
    React.useState<Category | null>(null)

  // 獲取所有類別（扁平化）
  const getAllCategories = (cats: Category[]): Category[] => {
    let result: Category[] = []
    cats.forEach((cat) => {
      result.push(cat)
      if (cat.children) {
        result = result.concat(getAllCategories(cat.children))
      }
    })
    return result
  }

  const allCategories = getAllCategories(categories)

  const handleCategorySubmit = async () => {
    if (!currentBotObjectId) return

    try {
      if (editingCategory) {
        const originalParentId = editingCategory.parentId || '0'
        const newParentId = categoryForm.parentId

        let apiParentId: number | null
        if (newParentId === originalParentId) {
          apiParentId = null // Not changed
        } else {
          apiParentId = Number(newParentId) // Changed (0 for root)
        }

        await updateCategory({
          bot_uuid: currentBot!.bot_detail_id,
          class_id: Number(editingCategory.id),
          category_name: categoryForm.name,
          category_description: categoryForm.description,
          parent_category_id: apiParentId
        }).unwrap()
        showSuccessToast(t('success.data_updated'))
      } else {
        await createCategory({
          bot_uuid: currentBot!.bot_detail_id,
          category_name: categoryForm.name,
          category_description: categoryForm.description,
          parent_category_id: Number(categoryForm.parentId) || 0
        }).unwrap()
        showSuccessToast(t('success.data_saved'))
      }
      getCategories(currentBot!.bot_detail_id)
      onCategoryDialogChange(false)
      onCategoryFormChange({ name: '', description: '', parentId: '0' })
      onEditingCategoryChange(null)
    } catch (error) {
      console.error('Category operation failed:', error)
    }
  }

  const handleDeleteCategoryConfirm = async () => {
    if (!currentBotObjectId || !currentDeleteCategory) return
    try {
      await deleteCategory({
        bot_uuid: currentBot!.bot_detail_id,
        deleted_class_id_list: [Number(currentDeleteCategory.id)]
      }).unwrap()
      showSuccessToast(t('success.data_deleted'))
      getCategories(currentBot!.bot_detail_id)
    } catch (error) {
      console.error('Delete category failed:', error)
    }
    setDeleteDialogOpen(false)
    setCurrentDeleteCategory(null)
  }

  const deleteCategoryItem = (category: Category) => {
    setCurrentDeleteCategory(category)
    setDeleteDialogOpen(true)
  }

  // 渲染類別樹
  const renderCategoryTree = (cats: Category[], level = 0) => {
    return cats.map((category) => (
      <Box key={category.id}>
        <ListItem
          sx={{
            pl: level * 3,
            borderRadius: 1,
            '&:hover': { bgcolor: 'action.hover' }
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            {category.children && category.children.length > 0 && (
              <IconButton
                size="small"
                onClick={() => {
                  const newExpanded = [...expandedCategories]
                  const index = newExpanded.indexOf(category.id)
                  if (index > -1) {
                    newExpanded.splice(index, 1)
                  } else {
                    newExpanded.push(category.id)
                  }
                  onExpandedCategoriesChange(newExpanded)
                }}
                sx={{ mr: 1 }}
              >
                {expandedCategories.includes(category.id) ? (
                  <ExpandMoreIcon fontSize="small" />
                ) : (
                  <ChevronRightIcon fontSize="small" />
                )}
              </IconButton>
            )}
            <Box
              sx={{
                flexGrow: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <Typography variant="body1" fontWeight="medium">
                {category.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ({category.description})
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <IconButton
                size="small"
                onClick={() => {
                  onEditingCategoryChange(category)
                  onCategoryFormChange({
                    name: category.name,
                    description: category.description,
                    parentId: category.parentId || '0'
                  })
                  onCategoryDialogChange(true)
                }}
              >
                <EditIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                onClick={() => deleteCategoryItem(category)}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>
        </ListItem>
        {category.children && (
          <Collapse in={expandedCategories.includes(category.id)}>
            <Box sx={{ ml: 2 }}>
              {renderCategoryTree(category.children, level + 1)}
            </Box>
          </Collapse>
        )}
      </Box>
    ))
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <CardHeader
          title={t('productManagementPage.categoryManagement')}
          action={
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                onEditingCategoryChange(null)
                onCategoryFormChange({
                  name: '',
                  description: '',
                  parentId: '0'
                })
                onCategoryDialogChange(true)
              }}
            >
              {t('productManagementPage.addCategory')}
            </Button>
          }
        />
        <CardContent sx={{ flex: 1, overflow: 'auto' }}>
          <List sx={{ width: '100%' }}>{renderCategoryTree(categories)}</List>
        </CardContent>
      </Card>

      <CustomDialog
        open={deleteDialogOpen}
        title={t('productManagementPage.deleteSingleTitle', {
          name: currentDeleteCategory?.name || ''
        })}
        handleClose={() => {
          setDeleteDialogOpen(false)
          setTimeout(() => {
            setCurrentDeleteCategory(null)
          }, 200)
        }}
        onSubmit={handleDeleteCategoryConfirm}
        dangerButton
      />

      {/* 類別對話框 */}
      <Dialog
        open={categoryDialog}
        onClose={() => onCategoryDialogChange(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editingCategory
            ? t('productManagementPage.editCategory')
            : t('productManagementPage.addCategory')}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('productManagementPage.categoryName')}
                value={categoryForm.name}
                onChange={(e) =>
                  onCategoryFormChange({
                    ...categoryForm,
                    name: e.target.value
                  })
                }
                disabled={isCreating || isUpdating}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('productManagementPage.categoryDescription')}
                multiline
                rows={3}
                value={categoryForm.description}
                onChange={(e) =>
                  onCategoryFormChange({
                    ...categoryForm,
                    description: e.target.value
                  })
                }
                disabled={isCreating || isUpdating}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>
                  {t('productManagementPage.parentCategory')}
                </InputLabel>
                <Select
                  value={categoryForm.parentId}
                  label={t('productManagementPage.parentCategory')}
                  onChange={(e) =>
                    onCategoryFormChange({
                      ...categoryForm,
                      parentId: e.target.value
                    })
                  }
                  disabled={isCreating || isUpdating}
                  renderValue={(selected) => {
                    if (selected === '0') {
                      return t('productManagementPage.rootCategory', 'Root')
                    }
                    const selectedCategory = allCategories.find(
                      (category) => category.id === selected
                    )
                    return selectedCategory?.name
                  }}
                >
                  <MenuItem value="0">
                    {t('productManagementPage.rootCategory', 'Root')}
                  </MenuItem>
                  {allCategories
                    .filter((c) => c.id !== editingCategory?.id)
                    .map((category) => (
                      <MenuItem key={category.id} value={category.id}>
                        {category.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => onCategoryDialogChange(false)}
            disabled={isCreating || isUpdating}
          >
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleCategorySubmit}
            variant="contained"
            disabled={isCreating || isUpdating || !categoryForm.name.trim()}
          >
            {(isCreating || isUpdating) && (
              <CircularProgress size={20} sx={{ mr: 1 }} />
            )}
            {editingCategory ? t('common.update') : t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CategoryManagement
