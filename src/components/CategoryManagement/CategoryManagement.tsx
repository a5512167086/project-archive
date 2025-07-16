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
  Typography
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'

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
  onCategoriesChange: (categories: Category[]) => void
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
  onCategoriesChange,
  onExpandedCategoriesChange,
  onCategoryDialogChange,
  onEditingCategoryChange,
  onCategoryFormChange
}) => {
  const { t } = useTranslation()

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

  const handleCategorySubmit = () => {
    const newCategory: Category = {
      id: editingCategory?.id || Date.now().toString(),
      ...categoryForm,
      parentId: categoryForm.parentId || undefined
    }

    if (editingCategory) {
      const updateCategory = (cats: Category[]): Category[] => {
        return cats.map((cat) => {
          if (cat.id === editingCategory.id) {
            return {
              ...cat,
              ...categoryForm,
              parentId: categoryForm.parentId || undefined
            }
          }
          if (cat.children) {
            return { ...cat, children: updateCategory(cat.children) }
          }
          return cat
        })
      }
      onCategoriesChange(updateCategory(categories))
    } else {
      if (categoryForm.parentId) {
        const addToParent = (cats: Category[]): Category[] => {
          return cats.map((cat) => {
            if (cat.id === categoryForm.parentId) {
              return {
                ...cat,
                children: [...(cat.children || []), newCategory]
              }
            }
            if (cat.children) {
              return { ...cat, children: addToParent(cat.children) }
            }
            return cat
          })
        }
        onCategoriesChange(addToParent(categories))
      } else {
        onCategoriesChange([...categories, newCategory])
      }
    }

    onCategoryDialogChange(false)
    onCategoryFormChange({ name: '', description: '', parentId: '' })
    onEditingCategoryChange(null)
  }

  const deleteCategory = (categoryId: string) => {
    const deleteCategoryRecursive = (cats: Category[]): Category[] => {
      return cats
        .filter((cat) => cat.id !== categoryId)
        .map((cat) => ({
          ...cat,
          children: cat.children
            ? deleteCategoryRecursive(cat.children)
            : undefined
        }))
    }
    onCategoriesChange(deleteCategoryRecursive(categories))
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
                    parentId: category.parentId || ''
                  })
                  onCategoryDialogChange(true)
                }}
              >
                <EditIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                onClick={() => deleteCategory(category.id)}
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
                  parentId: ''
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
                >
                  <MenuItem value="">
                    {t('productManagementPage.noParentCategory')}
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
          <Button onClick={() => onCategoryDialogChange(false)}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleCategorySubmit} variant="contained">
            {editingCategory ? t('common.update') : t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CategoryManagement
