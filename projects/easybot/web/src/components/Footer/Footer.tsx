import { StyledFooter } from './Footer.style'
import { Typography } from '@mui/material'

export const Footer = () => {
  return (
    <StyledFooter>
      <Typography>
        © {new Date().getFullYear()} Web Knowledge Extraction (WKE) Lab. All
        rights reserved.
      </Typography>
    </StyledFooter>
  )
}
