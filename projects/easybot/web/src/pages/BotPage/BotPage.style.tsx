import { styled } from '@mui/material/styles'
import { Container } from '@mui/material'

export const StyledBotPage = styled(Container)(() => ({}))

export const BotPageModalStyle = {
  modalBox: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    maxWidth: 600,
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4
  },
  modalDescription: {
    mt: 2,
    wordBreak: 'break-all'
  },
  modalButton: {
    mt: 3,
    textAlign: 'right'
  }
}
