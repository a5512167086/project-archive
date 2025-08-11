import { ProductImageResponse } from '@/store/apis/productApi'

export type ProductImageManagementProps = {
  images: ProductImageResponse[]
  productId: string
  onImagesUpdate: () => void
}
