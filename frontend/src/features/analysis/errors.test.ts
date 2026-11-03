import { ApiError } from '@/lib/api'
import { aiErrorText } from './errors'

test('a timeout shows the server message', () => {
  const message = 'GPT-OSS 120B took too long to answer. Try again or use Qwen 3.8 27B.'
  expect(aiErrorText(new ApiError(504, message))).toBe(message)
})

test('unknown failures get the generic text', () => {
  expect(aiErrorText(new Error('boom'))).toBe('Could not generate the AI analysis. Try again.')
})
