import { Link, LinkProps } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import { CustomLinkProps } from './CustomLink.type'
export const CustomLink = ({
  linkText,
  link,
  ...linkProps
}: CustomLinkProps & LinkProps) => {
  return (
    <Link component={RouterLink} to={link} {...linkProps}>
      {linkText}
    </Link>
  )
}
