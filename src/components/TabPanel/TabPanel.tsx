import { FC, ReactNode } from 'react'
import { Box } from '@mui/material'

interface TabPanelProps {
  children?: ReactNode
  index: number
  value: number
}

const TabPanel: FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      style={{ height: '100%' }}
      {...other}
    >
      {value === index && (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            overflow: 'hidden'
          }}
        >
          {children}
        </Box>
      )}
    </div>
  )
}

export default TabPanel
