export type NavItem = {
  text: string
  link: string
}

export type CustomDrawerProps = {
  navItems: NavItem[]
  isOpen: boolean
  handleDrawerToggle: () => void
}
