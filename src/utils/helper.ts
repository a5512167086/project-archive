import { OAuthActionType } from '@/configs/type'
import { BotsResponse } from '@/store/apis/botApi'
import { jwtDecode } from 'jwt-decode'

export const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export const isEmpty = (val: unknown) =>
  val === undefined ||
  val === null ||
  (Array.isArray(val) && val.length === 0) ||
  (typeof val === 'object' && Object.keys(val).length === 0) ||
  (typeof val === 'string' && val.trim().length === 0)

export const isTokenValid = (token: string) => {
  try {
    const decodedToken = jwtDecode(token)
    if (isEmpty(decodedToken)) {
      return false
    }
    const currentTime = Math.floor(Date.now() / 1000)
    if (!decodedToken.exp) {
      return false
    }
    return decodedToken.exp > currentTime
  } catch {
    clearUserToken()
    return false
  }
}

export const clearUserToken = () => {
  if (localStorage.getItem('access_token')) {
    localStorage.removeItem('access_token')
  }
  if (sessionStorage.getItem('access_token')) {
    sessionStorage.removeItem('access_token')
  }
}

export const getBotClassId = (
  botList: BotsResponse[],
  currentBotObjectId: number
) => {
  return botList
    .filter((bot) => bot.object_id === currentBotObjectId)
    .map((bot) => bot.class_id)[0]
}

export const isValidHttpUrl = (url: string): boolean => {
  try {
    const parsedUrl = new URL(url)
    return (
      (parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:') &&
      !!parsedUrl.hostname
    )
  } catch {
    return false
  }
}

export const handleGoogleOAuth = (action: OAuthActionType) => {
  const state = encodeURIComponent(
    JSON.stringify({ provider: 'google', action: action })
  )

  const client_id = import.meta.env.VITE_GOOGLE_CLIENT_ID
  const redirect_uri = `${location.origin}/oauth-callback`
  const scope =
    'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid'
  const response_type = 'code'
  const access_type = 'offline'

  const oauthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${client_id}&redirect_uri=${redirect_uri}&response_type=${response_type}&scope=${scope}&access_type=${access_type}&state=${state}`

  window.location.href = oauthUrl
}

export const handleLineOAuth = (action: OAuthActionType) => {
  const state = encodeURIComponent(
    JSON.stringify({ provider: 'line', action: action })
  )

  const client_id = import.meta.env.VITE_LINE_CLIENT_ID
  const redirect_uri = `${location.origin}/oauth-callback`
  const scope = 'profile%20openid%20email	'
  const response_type = 'code'
  const oauthUrl = `https://access.line.me/oauth2/v2.1/authorize?response_type=${response_type}&client_id=${client_id}&redirect_uri=${encodeURIComponent(
    redirect_uri
  )}&state=${state}&scope=${scope}`

  window.location.href = oauthUrl
}
