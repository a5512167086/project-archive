import { Box, Button, TextField, Typography } from '@mui/material'
import { StyledBotSettingPage } from './BotSettingPage.style'
import { CustomDivider } from '@/components/CustomDivider'

export const BotSettingPage = () => {
  return (
    <StyledBotSettingPage>
      <Typography variant="h5" className="setting__title">
        Bot設定
      </Typography>
      <Box className="setting__settingBox">
        <CustomDivider text="基本設定" />
        <Box className="setting__formBox" >
          <TextField
            required={true}
            margin="dense"
            label="Test"
            type="text"
            fullWidth
            variant="outlined"
          />
        </Box>
      </Box>
      <Box className="setting__settingBox">
        <CustomDivider text="危險區域" />
        <Box className="setting__dangerBox">
          <Typography>
            Delete this Bot
            <br />
            Once you delete a bot, there is no going back. Please be certain.
          </Typography>
          <Button variant="outlined" color="error">
            刪除帳號
          </Button>
        </Box>
      </Box>
    </StyledBotSettingPage>
  )
}
