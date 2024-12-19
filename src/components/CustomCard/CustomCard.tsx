import CardContent from '@mui/material/CardContent'
import CardMedia from '@mui/material/CardMedia'
import Typography from '@mui/material/Typography'
import CardActionArea from '@mui/material/CardActionArea'
import { StyledCustomCard, StyledSwitch } from './CustomCard.style'
import { ActionType, CustomCardProps } from './CustomCard.type'
import { Button, FormControlLabel, IconButton } from '@mui/material'
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
              <div className="card__imgBox">
                <CardMedia
                  component="img"
                  image={imgSrc}
                  className="card__img"
                />
              </div>
            )}
            <Typography variant="h5" component="div" className="card__title">
              {titleText}
            </Typography>
            <Typography component="div" className="card__description">
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
          <Typography component="div" className="card__description">
            {descriptionText}
          </Typography>
          {actionType === ActionType.Button && (
            <Button
              startIcon={buttonIcon}
              variant="outlined"
              className="card__button"
              onClick={buttonAction}
            >
              {buttonText}
            </Button>
          )}
          {actionType === ActionType.Switch && (
            <FormControlLabel
              value="start"
              control={<StyledSwitch sx={{ m: 1 }} color="primary" />}
              label={buttonText}
              className="card__switch"
              labelPlacement="start"
              checked={checked}
              onChange={(event) => {
                onSwitchClick?.((event.target as HTMLInputElement).checked)
              }}
            />
          )}
        </CardContent>
      )}
    </StyledCustomCard>
  )
}
