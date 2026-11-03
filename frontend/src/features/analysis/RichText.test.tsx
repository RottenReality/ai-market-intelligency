import { render, screen } from '@testing-library/react'
import { RichText } from './RichText'

test('numbers are bold and indicator citations become labels', () => {
  const { container } = render(
    <p>
      <RichText text="Colombia scores 52, with 92.1% using WhatsApp and $22,250 income [C2, E1]." />
    </p>,
  )
  const bold = [...container.querySelectorAll('strong')].map((el) => el.textContent)
  expect(bold).toEqual(['52', '92.1%', '$22,250'])
  expect(screen.getByText('C2')).toHaveAttribute('title', 'Indicator C2')
  expect(screen.getByText('E1')).toHaveAttribute('title', 'Indicator E1')
  expect(container.textContent).toBe(
    'Colombia scores 52, with 92.1% using WhatsApp and $22,250 incomeC2E1.',
  )
})

test('indicator IDs and words with digits are not treated as numbers', () => {
  const { container } = render(<RichText text="The G1 overlap and COVID19 notes." />)
  expect(container.querySelectorAll('strong')).toHaveLength(0)
})
