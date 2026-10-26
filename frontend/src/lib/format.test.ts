import { formatRaw, formatScore } from './format'

test.each([
  [79.345, '%', '79.3%'],
  [22250, 'USD', '$22,250'],
  [42090207, 'people', '42.1M'],
  [-0.1973526, 'index', '-0.20'],
  [3, 'hours', '3 h'],
  [true, 'bool', 'Yes'],
  [false, 'bool', 'No'],
  ['very_low', 'band', 'Very low'],
  [null, '%', 'n/a'],
] as const)('formatRaw(%s, %s) is %s', (value, unit, expected) => {
  expect(formatRaw(value, unit)).toBe(expected)
})

test('formatScore rounds to an integer and shows n/a for missing', () => {
  expect(formatScore(46.05)).toBe('46')
  expect(formatScore(74.5)).toBe('75')
  expect(formatScore(null)).toBe('n/a')
})
