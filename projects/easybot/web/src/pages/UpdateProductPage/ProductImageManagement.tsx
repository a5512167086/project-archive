import { useState } from 'react'
import {
  useCreateProductsImagesMutation,
  useDeleteProductsImagesMutation,
  useUpdateProductsImagesMutation,
  ProductImageResponse
} from '@/store/apis/productApi'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Button,
  IconButton,
  Card,
  CardMedia,
  Grid2,
  Chip
} from '@mui/material'
import {
  AddPhotoAlternate,
  Delete,
  Star,
  StarBorder
} from '@mui/icons-material'
import { CustomDialog } from '@/components/CustomDialog/CustomDialog'
import { showSuccessToast } from '@/utils/toast'
import { useAppSelector } from '@/utils/hook'
import { ProductImageManagementProps } from './ProductImageManagement.type'
import { FieldProps } from '@/components/CustomDialog/CustomDialog.type'
import { useParams } from 'react-router-dom'

const createProductImagesFields: FieldProps[] = [
  {
    id: 'images',
    name: 'images',
    label: 'productManagementPage.imageUpload',
    type: 'file',
    required: false,
    multiple: true,
    accept: 'image/*',
    defaultValue: null
  }
]

export const ProductImageManagement = ({
  images,
  productId,
  onImagesUpdate
}: ProductImageManagementProps) => {
  const { t } = useTranslation()
  const { uuid } = useParams()
  const { botList } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.bot_detail_id === uuid)
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [selectedImage, setSelectedImage] =
    useState<ProductImageResponse | null>(null)
  const [createImages] = useCreateProductsImagesMutation()
  const [deleteImage] = useDeleteProductsImagesMutation()
  const [updateImage] = useUpdateProductsImagesMutation()

  const handleAddImages = async (data: { images: File[] }) => {
    if (!data.images || data.images.length === 0 || !currentBot) return

    const filesArray = data.images
    await createImages({
      bot_uuid: currentBot.bot_detail_id,
      product_id: productId,
      images: filesArray
    }).unwrap()
    showSuccessToast('success.image_added', t)
    onImagesUpdate()
    setIsAddDialogOpen(false)
  }

  const handleDeleteImage = async () => {
    if (!selectedImage || !currentBot) return
    await deleteImage({
      bot_uuid: currentBot.bot_detail_id,
      image_id: selectedImage.image_id
    }).unwrap()
    showSuccessToast('success.image_deleted', t)
    onImagesUpdate()
    setIsDeleteDialogOpen(false)
    setSelectedImage(null)
  }

  const handleSetPrimaryImage = async (image: ProductImageResponse) => {
    if (!currentBot) return
    await updateImage({
      bot_uuid: currentBot.bot_detail_id,
      image_id: image.image_id,
      is_primary: true
    }).unwrap()
    showSuccessToast('success.primary_image_set', t)
    onImagesUpdate()
  }

  return (
    <Box>
      <Button
        variant="contained"
        startIcon={<AddPhotoAlternate />}
        onClick={() => setIsAddDialogOpen(true)}
        sx={{ mb: 2 }}
      >
        {t('productImage.addImages')}
      </Button>

      {images.length > 0 ? (
        <Grid2 container spacing={2}>
          {images.map((item) => (
            <Grid2 size={{ xs: 2 }} key={item.image_id}>
              <Card
                sx={{
                  width: '100%',
                  height: 280,
                  position: 'relative',
                  transition: '0.3s',
                  '&:hover': {
                    boxShadow: 6
                  }
                }}
              >
                <CardMedia
                  component="img"
                  height="280"
                  image={item.image_url}
                  alt={`Product Image ${item.image_id}`}
                  sx={{ objectFit: 'cover' }}
                />
                {item.is_primary && (
                  <Chip
                    label={t('productImage.primary')}
                    color="primary"
                    size="small"
                    sx={{ position: 'absolute', top: 8, left: 8 }}
                  />
                )}
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background:
                      'linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 70%, rgba(0,0,0,0) 100%)',
                    color: 'white',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'flex-end',
                    padding: '8px',
                    opacity: 0,
                    transition: 'opacity 0.3s',
                    '&:hover': {
                      opacity: 1
                    }
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <Box
                      sx={{ fontSize: '0.9rem' }}
                    >{`Image ${item.image_id}`}</Box>
                    <Box>
                      <IconButton
                        sx={{ color: 'white' }}
                        aria-label={`set primary image ${item.image_id}`}
                        onClick={() => handleSetPrimaryImage(item)}
                      >
                        {item.is_primary ? (
                          <Star sx={{ color: 'gold' }} />
                        ) : (
                          <StarBorder />
                        )}
                      </IconButton>
                      <IconButton
                        sx={{ color: 'white' }}
                        aria-label={`delete image ${item.image_id}`}
                        onClick={() => {
                          setSelectedImage(item)
                          setIsDeleteDialogOpen(true)
                        }}
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </Box>
                </Box>
              </Card>
            </Grid2>
          ))}
        </Grid2>
      ) : (
        <Box sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>
          {t('productImage.noImagesAdded')}
        </Box>
      )}

      <CustomDialog
        open={isAddDialogOpen}
        handleClose={() => setIsAddDialogOpen(false)}
        title={t('productImage.addImages')}
        onSubmit={handleAddImages}
        fields={createProductImagesFields}
      />

      {selectedImage && (
        <CustomDialog
          open={isDeleteDialogOpen}
          handleClose={() => {
            setIsDeleteDialogOpen(false)
            setSelectedImage(null)
          }}
          title={t('productImage.deleteImageTitle', {
            id: selectedImage.image_id
          })}
          onSubmit={handleDeleteImage}
        />
      )}
    </Box>
  )
}
