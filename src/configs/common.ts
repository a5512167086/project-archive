export const LANGUAGES = {
  EN: { title: 'English', value: 'en' },
  ZH: { title: '中文', value: 'zh' }
}

export const ERROR_CODE_MESSAGE_MAPPING = {
  USER_ALREADY_EXISTS: 'error.user_already_exists',
  USER_NOT_EXISTS: 'error.user_not_found',
  PASSWORD_NOT_MATCH: 'error.password_not_match',
  OAUTH_FAILED: 'error.oauth_failed',
  USER_LOOKUP_FAILED: 'error.unknown_error',
  USER_CREATION_FAILED: 'error.unknown_error',
  EMAIL_SERVICE_FAILED: 'error.unknown_error',
  INVALID_LINE_BOT: 'error.invalid_line_bot'
}

export const SELECT_LANGUAGES_LIST = [LANGUAGES.EN, LANGUAGES.ZH]
