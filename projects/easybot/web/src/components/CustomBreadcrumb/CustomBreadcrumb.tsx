import { Breadcrumbs } from '@mui/material'
import { CustomLink } from '@/components/CustomLink'
import { useTranslation } from 'react-i18next'

interface BreadcrumbItem {
  link: string
  linkText: string
  color?: string
}

interface CustomBreadcrumbProps {
  items: BreadcrumbItem[]
  sx?: object
}

export const CustomBreadcrumb = ({ items, sx }: CustomBreadcrumbProps) => {
  const { t } = useTranslation()

  return (
    <Breadcrumbs
      sx={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '20px 0', ...sx }}
    >
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        return (
          <CustomLink
            key={index}
            link={item.link}
            linkText={t(item.linkText)}
            color={isLast ? 'text.primary' : 'inherit'}
            aria-current={isLast ? 'page' : undefined}
          />
        )
      })}
    </Breadcrumbs>
  )
}
