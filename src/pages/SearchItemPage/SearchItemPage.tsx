import { Box, Typography, Card, CardContent } from '@mui/material'
import { useAppSelector } from '@/utils/hook'
import Slider from 'react-slick'

export const SearchItemPage = () => {
  const { searchItems, currentSearchItemObjectId } = useAppSelector(
    (state) => state.search
  )

  const currentSearchItem = searchItems.find(
    (item) => item.object_id === currentSearchItemObjectId
  )

  if (!currentSearchItem) {
    return (
      <Box textAlign="center" mt={5}>
        <Typography variant="h5">No item found</Typography>
      </Box>
    )
  }

  const {
    chinese_name,
    english_name,
    type,
    description,
    price,
    instruction,
    ingredient,
    url,
    images
  } = currentSearchItem

  const sliderSettings = {
    dots: true,
    infinite: true,
    speed: 500,
    slidesToShow: 1,
    slidesToScroll: 1
  }

  return (
    <Box p={3} maxWidth="xl" mx="auto">
      <Card>
        <CardContent>
          <Typography variant="subtitle1" color="text.secondary" mb={2}>
            {chinese_name}
          </Typography>
          <Typography variant="h5" mb={2}>
            {english_name}
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Type: {type}
          </Typography>
          <Typography variant="body1" mb={2}>
            Description: {description}
          </Typography>
          <Typography variant="body1" mb={2}>
            Price: {price}
          </Typography>
          <Typography variant="body1" mb={2}>
            Instruction: {instruction}
          </Typography>
          <Typography variant="body1" mb={2}>
            Ingredient: {ingredient}
          </Typography>
          {url && (
            <Typography variant="body1" mb={2}>
              URL:{' '}
              <a href={url} target="_blank" rel="noopener noreferrer">
                {url}
              </a>
            </Typography>
          )}
          {images && images.length > 0 && (
            <Box p={2}>
              <Slider {...sliderSettings}>
                {images.map((image, index) => (
                  <Box key={index} textAlign="center">
                    <img
                      src={image.image_src}
                      alt={`Image ${index + 1}`}
                      style={{
                        maxHeight: '300px',
                        margin: '0 auto',
                        display: 'block',
                        objectFit: 'contain'
                      }}
                    />
                    {image.ocr_text && (
                      <Typography variant="caption" display="block" mt={1}>
                        {image.ocr_text}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Slider>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
