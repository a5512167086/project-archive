import { Suspense, useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Toolbar from '@mui/material/Toolbar'
import List from '@mui/material/List'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import MenuIcon from '@mui/icons-material/Menu'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import LogoIcon from '@/assets/header_logo.svg?react'
import { Outlet, useNavigate, useParams } from 'react-router-dom' // 確保引入 useParams
import {
  StyledDrawerHeader,
  StyledDrawer,
  StyledSidebarHeader
} from './SidebarWrapper.style'
import { useLazyGetBotsQuery } from '@/store/apis/botApi'
import { LanguageChanger } from '../LanguageChanger'
import { Button } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useUser } from '@/hooks/useUser'
import { CustomLoader } from '../CustomLoader'
import { PAGE_PATHS, SIDEBAR_NAVIGATION_ROUTE } from '@/routes'
import { useAppSelector } from '@/utils/hook'
import { useHandleAuthRedirect } from '@/hooks/useHandleAuthRedirect'
import { CustomAlert } from '../CustomAlert/CustomAlert'
import { useErrorHandler } from '@/hooks/useErrorHandler'

const sidebarWrapperContent = {
  logout: 'header.signOut',
  loaderText: 'common.loading'
}

export const SidebarWrapper = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()

  const { uuid } = useParams()
  const { botList } = useAppSelector((state) => state.bot)
  const currentBot = botList.find((bot) => bot.bot_detail_id === uuid)

  const { isAuthenticated } = useAppSelector((state) => state.user)
  const { isAuthFailed, setIsAuthFailed, logout } = useUser()
  const [open, setOpen] = useState(false)
  const [isAlertOpen, setAlertOpen] = useState(false)
  const [getBots, { isLoading: isFetchingBots }] = useLazyGetBotsQuery() // 加上 loading 狀態

  useErrorHandler()

  const handleAuthFailed = () => {
    setAlertOpen(true)
    setIsAuthFailed(false)
  }

  useHandleAuthRedirect(isAuthenticated, isAuthFailed, handleAuthFailed)

  const handleDrawerOpen = () => {
    setOpen(true)
  }

  const handleDrawerClose = () => {
    setOpen(false)
  }

  const handleNavigate = (routeLink: string, key: string) => {
    if (key === 'backToBotList') {
      navigate(PAGE_PATHS.BOT_LIST)
      return
    }

    if (key === 'moduleList') {
      navigate(`/bot-list/${uuid}`)
      return
    }
    navigate(`/bot-list/${uuid}/${routeLink}`)
  }

  useEffect(() => {
    const fetchBotsIfNeeded = async () => {
      if (botList.length === 0) {
        await getBots().unwrap()
      }
    }
    fetchBotsIfNeeded()
  }, [botList.length, getBots])

  if (!currentBot) {
    if (botList.length === 0 || isFetchingBots) {
      return (
        <CustomLoader size="100vh" text={t(sidebarWrapperContent.loaderText)} />
      )
    }

    return (
      <Box
        sx={{
          p: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}
      >
        <Typography variant="h5">Bot Not Found</Typography>
        <Button onClick={() => navigate(PAGE_PATHS.BOT_LIST)}>
          Back to List
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <StyledSidebarHeader position="fixed" open={open}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerOpen}
            edge="start"
            sx={{
              marginRight: 5,
              display: open ? 'none' : null
            }}
          >
            <MenuIcon />
          </IconButton>
          <LogoIcon className="header__logo" />

          <Typography variant="h6" component="div" className="header__title">
            {currentBot.chinese_name || 'EasyBot'}
          </Typography>

          <Button className="header__navLink" onClick={logout}>
            {t(sidebarWrapperContent.logout)}
          </Button>
          <LanguageChanger />
        </Toolbar>
      </StyledSidebarHeader>

      <StyledDrawer variant="permanent" open={open}>
        <StyledDrawerHeader>
          <IconButton onClick={handleDrawerClose}>
            <ChevronLeftIcon />
          </IconButton>
        </StyledDrawerHeader>
        <Divider />
        <List>
          {SIDEBAR_NAVIGATION_ROUTE.map((group, groupIndex) => (
            <Box key={group.key}>
              {group.items.map((route) => (
                <ListItem
                  key={route.key}
                  disablePadding
                  sx={{ display: 'block' }}
                >
                  <ListItemButton
                    onClick={() => handleNavigate(route.link, route.key)}
                    sx={{
                      minHeight: 48,
                      px: 2.5,
                      justifyContent: open ? 'initial' : 'center'
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        justifyContent: 'center',
                        mr: open ? 3 : 'auto'
                      }}
                    >
                      {route.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={t(route.text)}
                      sx={{ opacity: open ? 1 : 0 }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
              {groupIndex < SIDEBAR_NAVIGATION_ROUTE.length - 1 && <Divider />}
            </Box>
          ))}
        </List>
      </StyledDrawer>

      <Box
        component="main"
        className="wrapper__content"
        sx={{ flexGrow: 1, paddingX: 3 }}
      >
        <StyledDrawerHeader />
        <Suspense
          fallback={
            <CustomLoader
              size="6rem"
              text={t(sidebarWrapperContent.loaderText)}
            />
          }
        >
          <Outlet />
          <CustomAlert
            open={isAlertOpen}
            message={t('error.token_expired')}
            onClose={() => setAlertOpen(false)}
          />
        </Suspense>
      </Box>
    </Box>
  )
}
