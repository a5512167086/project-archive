import { useState } from 'react'
import {
  AppBar,
  Box,
  IconButton,
  Toolbar,
  Typography,
  Button
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import LogoIcon from '@/assets/header_logo.svg?react'
import { StyledHeader } from './Header.style'
import { CustomDrawer } from '@/components/CustomDrawer'
import { PRIVATE_NAVIGATION_ROUTE, PUBLIC_NAVIGATION_ROUTE } from '@/routes'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LanguageChanger } from '../LanguageChanger'
import { useUser } from '@/hooks/useUser'
import { useAppSelector } from '@/utils/hook'

const headerContent = { logout: 'header.signOut' }

export const Header = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAppSelector((state) => state.user)
  const { t } = useTranslation()
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const { logout } = useUser()
  const handleDrawerToggle = () => {
    setIsDrawerOpen((prevState) => !prevState)
  }

  const handleNavigation = (link: string) => {
    navigate(link)
  }

  return (
    <StyledHeader>
      <AppBar component="nav" position="fixed">
        <Toolbar sx={{ height: '100%' }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={(theme) => ({
              marginRight: '20px',
              [theme.breakpoints.up('sm')]: {
                display: 'none'
              }
            })}
          >
            <MenuIcon />
          </IconButton>
          <Box>
            <LogoIcon className="header__logo" />
          </Box>
          <Typography
            variant="h6"
            component="div"
            sx={(theme) => ({
              flexGrow: 1,
              fontSize: '1.75rem',
              [theme.breakpoints.down('sm')]: {
                textAlign: 'center',
                paddingRight: '45px'
              },
              [theme.breakpoints.up('sm')]: {
                display: 'block'
              }
            })}
          >
            EasyBot
          </Typography>
          <Box
            sx={(theme) => ({
              [theme.breakpoints.down('sm')]: {
                display: 'none'
              },
              [theme.breakpoints.up('sm')]: {
                display: 'block'
              }
            })}
          >
            {!isAuthenticated ? (
              PUBLIC_NAVIGATION_ROUTE.map((item) => (
                <Button
                  key={t(item.text)}
                  sx={{ color: (theme) => theme.palette.common.white }}
                  onClick={() => {
                    handleNavigation(item.link)
                  }}
                >
                  {t(item.text)}
                </Button>
              ))
            ) : (
              <>
                {PRIVATE_NAVIGATION_ROUTE.map((item) => (
                  <Button
                    key={t(item.text)}
                    sx={{ color: (theme) => theme.palette.common.white }}
                    onClick={() => {
                      handleNavigation(item.link)
                    }}
                  >
                    {t(item.text)}
                  </Button>
                ))}
                <Button
                  onClick={logout}
                  sx={{ color: (theme) => theme.palette.common.white }}
                >
                  {t(headerContent.logout)}
                </Button>
              </>
            )}
            <LanguageChanger />
          </Box>
        </Toolbar>
      </AppBar>
      <nav>
        {!isAuthenticated ? (
          <CustomDrawer
            navItems={PUBLIC_NAVIGATION_ROUTE}
            isOpen={isDrawerOpen}
            handleDrawerToggle={handleDrawerToggle}
          />
        ) : (
          <CustomDrawer
            navItems={PRIVATE_NAVIGATION_ROUTE}
            isOpen={isDrawerOpen}
            handleDrawerToggle={handleDrawerToggle}
          />
        )}
      </nav>
    </StyledHeader>
  )
}
