export const LANGUAGES = {
  EN: { title: 'English', value: 'en' },
  ZH: { title: '中文', value: 'zh' }
}

export const ERROR_CODE_MESSAGE_MAPPING = {
  // User related errors
  USER_NOT_EXISTS: 'error.user_not_found',
  USER_ALREADY_EXISTS: 'error.user_already_exists',
  PASSWORD_NOT_MATCH: 'error.password_not_match',
  USER_LOOKUP_FAILED: 'error.user_lookup_failed',
  USER_CREATION_FAILED: 'error.user_creation_failed',

  // OAuth related errors
  OAUTH_ALREADY_EXISTS: 'error.oauth_already_exists',
  USER_ALREADY_BINDED: 'error.user_already_binded',
  OAUTH_FAILED: 'error.oauth_failed',
  OAUTH_PROVIDER_NOT_SUPPORTED: 'error.oauth_provider_not_supported',

  // Email and token related errors
  EMAIL_SERVICE_FAILED: 'error.email_service_failed',
  TOKEN_EXPIRED: 'error.token_expired',
  TOKEN_INVALID: 'error.token_invalid',
  TOKEN_PAYLOAD_INVALID: 'error.token_payload_invalid',

  // Bot related errors
  BOT_NOT_EXIST: 'error.bot_not_exist',
  BOT_PERMISSION_DENIED: 'error.bot_permission_denied',
  CREATE_LIFF_APP_FAILED: 'error.create_liff_app_failed',
  GET_CHANNEL_ACCESS_TOKEN_FAILED: 'error.get_channel_access_token_failed',
  INVALID_LINE_BOT: 'error.invalid_line_bot',
  NO_UPDATE_DATA: 'error.no_update_data',
  EMPTY_BOT_UUID: 'error.empty_bot_uuid',
  EMPTY_CREDENTIALS: 'error.empty_credentials',
  EMPTY_X_LINE_SIGNATURE: 'error.empty_x_line_signature',

  // Group related errors
  GROUP_NOT_EXIST: 'error.group_not_exist',
  USER_NOT_IN_BOT_GROUP: 'error.user_not_in_bot_group',

  // Knowledge related errors
  KNOWLEDGE_CLASS_NOT_FOUND: 'error.knowledge_class_not_found',
  INVALID_FILE_TYPE: 'error.invalid_file_type',
  INVALID_CSV_FORMAT: 'error.invalid_csv_format',
  EMPTY_DELETE_LIST: 'error.empty_delete_list',

  // Setting related errors
  SETTING_CLASS_NOT_FOUND: 'error.setting_class_not_found',

  // Reservation related errors
  SERVICE_CLASS_NOT_FOUND: 'error.service_class_not_found',
  RESERVATION_CLASS_NOT_FOUND: 'error.reservation_class_not_found',
  SERVICE_NOT_FOUND: 'error.service_not_found',
  RESERVATION_SCHEDULE_NOT_FOUND: 'error.reservation_schedule_not_found',
  RESERVATION_TIME_INVALID: 'error.reservation_time_invalid',
  RESERVATION_CAPACITY_EXCEEDED: 'error.reservation_capacity_exceeded',
  RESERVATION_OPTION_INVALID: 'error.reservation_option_invalid',
  RESERVATION_NOT_FOUND: 'error.reservation_not_found',

  // Brand related errors
  BRAND_CLASS_NOT_FOUND: 'error.brand_class_not_found',
  BRAND_NOT_FOUND: 'error.brand_not_found',
  BRAND_ALREADY_EXISTS: 'error.brand_already_exists',

  // Category related errors
  CATEGORY_CLASS_NOT_FOUND: 'error.category_class_not_found',
  CATEGORY_NOT_FOUND: 'error.category_not_found',
  CATEGORY_ALREADY_EXISTS: 'error.category_already_exists',
  PARENT_CATEGORY_NOT_FOUND: 'error.parent_category_not_found',
  INVALID_CATEGORY_HIERARCHY: 'error.invalid_category_hierarchy',

  // Product related errors
  PRODUCT_CLASS_NOT_FOUND: 'error.product_class_not_found',
  PRODUCT_NOT_FOUND: 'error.product_not_found',
  PRODUCT_SKU_ALREADY_EXISTS: 'error.product_sku_already_exists',

  // File and storage related errors
  MINIO_UPLOAD_ERROR: 'error.minio_upload_error',
  MINIO_DELETE_ERROR: 'error.minio_delete_error',

  // General errors
  INTERNAL_SERVER_ERROR: 'error.internal_server_error',
  INVALID_INPUT: 'error.invalid_input'
}

export const SELECT_LANGUAGES_LIST = [LANGUAGES.EN, LANGUAGES.ZH]
