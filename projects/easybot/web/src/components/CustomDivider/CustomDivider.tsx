import { StyledDivider } from './CustomDivider.style'
import { CustomDividerProps } from './CustomDivider.type'

export const CustomDivider = ({ text }: CustomDividerProps) => {
  return (
    <StyledDivider>
      <div className="divider__line" />
      {text && <div className="divider__text">{text}</div>}
      <div className="divider__line" />
    </StyledDivider>
  )
}
