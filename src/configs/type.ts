export type CustomError = {
  error_code: string
  error_message: string
}

export type HttpResponse = {
  status: number
  data: object
}

export enum OAuthActionType {
  Login = 'login',
  Bind = 'bind'
}
