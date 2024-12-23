import { ReactNode } from 'react'

export enum ActionType {
  Button = 'button',
  Switch = 'switch'
}

export interface CustomCardProps {
  imgSrc?: string
  enableHeaderButton?: boolean
  cardButton?: boolean
  cardButtonAction?: () => void
  titleText: string
  descriptionText?: string
  actionType?: ActionType
  buttonText?: string
  buttonIcon?: ReactNode
  buttonAction?: () => void
  checked?: boolean
  onSwitchClick?: (checked: boolean) => void
}
