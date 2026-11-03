import { formatScore } from './format'

test('formatScore rounds to an integer and shows n/a for missing', () => {
  expect(formatScore(46.05)).toBe('46')
  expect(formatScore(74.5)).toBe('75')
  expect(formatScore(null)).toBe('n/a')
})
