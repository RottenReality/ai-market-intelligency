import { splitSentences } from './sentences'

test('splits sentences but not decimals, money or citations', () => {
  const text =
    'The cultural score is low at 23. Furthermore, 92.1% of internet users use WhatsApp [C2]. ' +
    'Income is $22,250 per person [E1]! Is it enough? Yes.'
  expect(splitSentences(text)).toEqual([
    'The cultural score is low at 23.',
    'Furthermore, 92.1% of internet users use WhatsApp [C2].',
    'Income is $22,250 per person [E1]!',
    'Is it enough?',
    'Yes.',
  ])
})

test('a single sentence or empty text', () => {
  expect(splitSentences('Only one sentence [A1]')).toEqual(['Only one sentence [A1]'])
  expect(splitSentences('  ')).toEqual([])
})
