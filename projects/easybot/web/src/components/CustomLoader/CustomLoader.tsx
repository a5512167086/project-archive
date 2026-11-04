import { CircularProgress, CircularProgressProps } from '@mui/material'
import { CustomLoaderProps } from './CustomLoader.type'
import { StyledCustomLoader } from './CustomLoader.style'
export const CustomLoader = ({
  size,
  text
}: CustomLoaderProps & CircularProgressProps) => {
  return (
    <StyledCustomLoader>
      <CircularProgress size={size} />
      {text && <div>{text}</div>}
    </StyledCustomLoader>
  )
}
