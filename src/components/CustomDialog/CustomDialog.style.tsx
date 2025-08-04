import { Dialog, styled } from '@mui/material'

export const StyledDialog = styled(Dialog)(() => ({
  '& .dialog__actionButton': {
    marginLeft: '8px'
  }
}))

export const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1
})
