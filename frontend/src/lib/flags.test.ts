import { flagEmoji } from './flags'

test('turns an ISO3 code into its flag emoji', () => {
  expect(flagEmoji('COL')).toBe('🇨🇴')
  expect(flagEmoji('esp')).toBe('🇪🇸')
  expect(flagEmoji('USA')).toBe('🇺🇸')
})

test('unknown codes have no flag', () => {
  expect(flagEmoji('XYZ')).toBe('')
})
