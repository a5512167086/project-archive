import CardContent from '@mui/material/CardContent'
import CardMedia from '@mui/material/CardMedia'
import Typography from '@mui/material/Typography'
import CardActionArea from '@mui/material/CardActionArea'
import { StyledCustomCard, StyledSwitch } from './CustomCard.style'
import { ActionType, CustomCardProps } from './CustomCard.type'
import { Box, Button, FormControlLabel, IconButton } from '@mui/material'
import SettingsIcon from '@mui/icons-material/Settings'

export const CustomCard = ({
  imgSrc,
  enableHeaderButton,
  cardButton,
  cardButtonAction,
  titleText,
  descriptionText,
  actionType,
  buttonText,
  buttonIcon,
  buttonAction,
  checked,
  onSwitchClick
}: CustomCardProps) => {
  return (
    <StyledCustomCard>
      {enableHeaderButton && (
        <IconButton className="card__headerButton">
          <SettingsIcon />
        </IconButton>
      )}
      {cardButton ? (
        <CardActionArea className="card__actionArea" onClick={cardButtonAction}>
          <CardContent className="card__content">
            {imgSrc && (
              <Box className="card__imgBox">
                <CardMedia
                  component="img"
                  image={imgSrc}
                  className="card__img"
                />
              </Box>
            )}
            <Typography variant="h5" component="div" className="card__title">
              {titleText}
            </Typography>
            <Typography
              component="div"
              sx={{
                width: '100%',
                padding: '0 10px',
                textAlign: 'left'
              }}
            >
              {descriptionText}
            </Typography>
          </CardContent>
        </CardActionArea>
      ) : (
        <CardContent className="card__content">
          {imgSrc && (
            <div className="card__imgBox">
              <CardMedia component="img" image={imgSrc} className="card__img" />
            </div>
          )}
          <Typography variant="h5" component="div" className="card__title">
            {titleText}
          </Typography>
          <Typography
            component="div"
            sx={{
              width: '100%',
              padding: '0 10px',
              textAlign: 'left'
            }}
          >
            {descriptionText}
          </Typography>
          {actionType === ActionType.Button && (
            <Button
              startIcon={buttonIcon}
              variant="outlined"
              onClick={buttonAction}
              sx={{
                fontWeight: 'bold',
                fontSize: '1rem',
                padding: '5px 10px'
              }}
            >
              {buttonText}
            </Button>
          )}
          {actionType === ActionType.Switch && (
            <FormControlLabel
              value="start"
              control={<StyledSwitch sx={{ m: 1 }} color="primary" />}
              label={buttonText}
              labelPlacement="start"
              checked={checked}
              onChange={(event) => {
                onSwitchClick?.((event.target as HTMLInputElement).checked)
              }}
              sx={{
                '& .MuiFormControlLabel-label': {
                  fontWeight: 'bold',
                  fontSize: '1.25rem'
                }
              }}
            />
          )}
        </CardContent>
      )}
    </StyledCustomCard>
  )
}
