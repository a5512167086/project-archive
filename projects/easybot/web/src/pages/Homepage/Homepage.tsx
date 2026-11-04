import { Hero } from '@/components/Hero'
import { StyledHomePage } from './Homepage.style'
import { FeatureOverview } from '@/components/FeatureOverview'

const Homepage = () => {
  return (
    <StyledHomePage maxWidth="lg" disableGutters>
      <Hero />
      <FeatureOverview />
    </StyledHomePage>
  )
}

export default Homepage
