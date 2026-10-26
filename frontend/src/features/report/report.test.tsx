import { render, screen } from '@testing-library/react'
import { ExportPdfButton } from './ExportPdfButton'

test('export link targets the selected countries', () => {
  render(<ExportPdfButton iso3={['COL', 'MEX']} />)
  const link = screen.getByRole('link', { name: 'Export PDF' })
  expect(link).toHaveAttribute('href', '/api/reports/pdf?iso3=COL%2CMEX')
  expect(link).toHaveAttribute('download')
})
