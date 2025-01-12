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

const headerContent = { logout: 'header.signOut' }

export const Header = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const { isAuthenticated, logout } = useUser()
  const handleDrawerToggle = () => {
    setIsDrawerOpen((prevState) => !prevState)
  }

  const handleNavigation = (link: string) => {
    navigate(link)
  }

  return (
    <StyledHeader>
      <AppBar component="nav" position="fixed">
        <Toolbar className="header__toolbar">
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            className="header__iconButton"
          >
            <MenuIcon />
          </IconButton>
          <LogoIcon className="header__logo" />
          <Typography variant="h6" component="div" className="header__title">
            EasyBot
          </Typography>
          <Box className="header__navBox">
            {!isAuthenticated ? (
              PUBLIC_NAVIGATION_ROUTE.map((item) => (
                <Button
                  key={t(item.text)}
                  className="header__navLink"
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
                    className="header__navLink"
                    onClick={() => {
                      handleNavigation(item.link)
                    }}
                  >
                    {t(item.text)}
                  </Button>
                ))}
                <Button className="header__navLink" onClick={logout}>
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
