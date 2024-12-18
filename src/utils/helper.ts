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
  if (localStorage.getItem('token')) {
    localStorage.removeItem('token')
  }
  if (sessionStorage.getItem('token')) {
    sessionStorage.removeItem('token')
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
