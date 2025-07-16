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
  Grid
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { CustomTable } from '@/components/CustomTable'

interface Brand {
  id: string
  name: string
  description: string
  logo?: string
}

interface BrandForm {
  name: string
  description: string
}

interface BrandManagementProps {
  brands: Brand[]
  selectedBrands: number[]
  brandDialog: boolean
  editingBrand: Brand | null
  brandForm: BrandForm
  onBrandsChange: (brands: Brand[]) => void
  onSelectedBrandsChange: React.Dispatch<React.SetStateAction<number[]>>
  onBrandDialogChange: (open: boolean) => void
  onEditingBrandChange: (brand: Brand | null) => void
  onBrandFormChange: (form: BrandForm) => void
}

const BrandManagement: React.FC<BrandManagementProps> = ({
  brands,
  selectedBrands,
  brandDialog,
  editingBrand,
  brandForm,
  onBrandsChange,
  onSelectedBrandsChange,
  onBrandDialogChange,
  onEditingBrandChange,
  onBrandFormChange
}) => {
  const { t } = useTranslation()

  // 品牌表格列定義
  const brandColumns = [
    { id: 'name', label: 'productManagementPage.brandName' },
    { id: 'description', label: 'productManagementPage.description' }
  ]

  const handleBrandSubmit = () => {
    if (editingBrand) {
      onBrandsChange(
        brands.map((b) =>
          b.id === editingBrand.id ? { ...editingBrand, ...brandForm } : b
        )
      )
    } else {
      onBrandsChange([...brands, { id: Date.now().toString(), ...brandForm }])
    }
    onBrandDialogChange(false)
    onBrandFormChange({ name: '', description: '' })
    onEditingBrandChange(null)
  }

  const deleteBrand = (brand: Brand) => {
    onBrandsChange(brands.filter((b) => b.id !== brand.id))
  }

  const handleDeleteSelectedBrands = () => {
    const selectedBrandIds = selectedBrands.map((index) => brands[index].id)
    onBrandsChange(
      brands.filter((brand) => !selectedBrandIds.includes(brand.id))
    )
    onSelectedBrandsChange([])
  }

  const handleEditBrand = (brand: Brand) => {
    onEditingBrandChange(brand)
    onBrandFormChange({ name: brand.name, description: brand.description })
    onBrandDialogChange(true)
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <CardHeader
          title={t('productManagementPage.brandManagement')}
          action={
            <Box display="flex" gap={2}>
              {selectedBrands.length > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleDeleteSelectedBrands}
                >
                  {t('productManagementPage.deleteSelected')}
                </Button>
              )}
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  onEditingBrandChange(null)
                  onBrandFormChange({ name: '', description: '' })
                  onBrandDialogChange(true)
                }}
              >
                {t('productManagementPage.addBrand')}
              </Button>
            </Box>
          }
        />
        <CardContent
          sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}
          className="product__tableContainer"
        >
          <CustomTable
            data={brands}
            columns={brandColumns}
            selected={selectedBrands}
            setSelected={onSelectedBrandsChange}
            onEdit={handleEditBrand}
            onDelete={deleteBrand}
          />
        </CardContent>
      </Card>

      {/* 品牌對話框 */}
      <Dialog
        open={brandDialog}
        onClose={() => onBrandDialogChange(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editingBrand
            ? t('productManagementPage.editBrand')
            : t('productManagementPage.addBrand')}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('productManagementPage.brandName')}
                value={brandForm.name}
                onChange={(e) =>
                  onBrandFormChange({ ...brandForm, name: e.target.value })
                }
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('productManagementPage.brandDescription')}
                multiline
                rows={3}
                value={brandForm.description}
                onChange={(e) =>
                  onBrandFormChange({
                    ...brandForm,
                    description: e.target.value
                  })
                }
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => onBrandDialogChange(false)}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleBrandSubmit} variant="contained">
            {editingBrand ? t('common.update') : t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default BrandManagement
