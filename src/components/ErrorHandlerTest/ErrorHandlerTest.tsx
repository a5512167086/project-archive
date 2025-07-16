import { Button } from '@mui/material'
import { useAppDispatch, useAppSelector } from '@/utils/hook'
import { setBotError } from '@/store/modules/botSlice'
import { setBrandError } from '@/store/modules/brandSlice'
import { useErrorHandler } from '@/hooks/useErrorHandler'

/**
 * 用於測試 useErrorHandler 的組件
 * 這個組件可以手動觸發不同類型的錯誤來測試 hook 是否正常工作
 */
export const ErrorHandlerTest = () => {
  const dispatch = useAppDispatch()
  const { errorCode: botErrorCode } = useAppSelector((state) => state.bot)
  const { errorCode: brandErrorCode } = useAppSelector((state) => state.brand)

  // 使用錯誤處理 hook
  useErrorHandler()

  const triggerBotError = () => {
    console.log('Triggering bot error...')
    dispatch(setBotError({
      error_code: 'TEST_BOT_ERROR',
      error_message: 'This is a test bot error'
    }))
  }

  const triggerBrandError = () => {
    console.log('Triggering brand error...')
    dispatch(setBrandError({
      error_code: 'TEST_BRAND_ERROR',
      error_message: 'This is a test brand error'
    }))
  }

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', margin: '20px' }}>
      <h3>Error Handler Test</h3>
      <p>Current Bot Error: {botErrorCode || 'None'}</p>
      <p>Current Brand Error: {brandErrorCode || 'None'}</p>
      
      <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
        <Button variant="contained" color="error" onClick={triggerBotError}>
          Trigger Bot Error
        </Button>
        <Button variant="contained" color="error" onClick={triggerBrandError}>
          Trigger Brand Error
        </Button>
      </div>
      
      <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
        <p>開啟瀏覽器開發者工具的 Console 來查看調試信息</p>
        <p>如果 useErrorHandler 正常工作，點擊按鈕後應該會顯示 toast 通知</p>
      </div>
    </div>
  )
}
