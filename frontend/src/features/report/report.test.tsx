import { render, screen } from '@testing-library/react'
import { ExportPdfButton } from './ExportPdfButton'

test('export link targets the selected countries', () => {
  render(<ExportPdfButton iso3={['COL', 'MEX']} missingAnalyses={0} />)
  const link = screen.getByRole('link', { name: 'Export PDF' })
  expect(link).toHaveAttribute('href', '/api/reports/pdf?iso3=COL%2CMEX')
  expect(link).toHaveAttribute('download')
})

test('shows note when analyses are missing', () => {
  render(<ExportPdfButton iso3={['COL', 'MEX', 'ESP', 'CHL']} missingAnalyses={2} />)
  expect(screen.getByText('2 of 4 countries have no AI analysis yet')).toBeInTheDocument()
})

test('no note when all have analyses', () => {
  render(<ExportPdfButton iso3={['COL', 'MEX']} missingAnalyses={0} />)
  expect(screen.queryByText(/no AI analysis yet/)).not.toBeInTheDocument()
})

test('single-country wording', () => {
  render(<ExportPdfButton iso3={['COL']} missingAnalyses={1} />)
  expect(screen.getByText('This country has no AI analysis yet')).toBeInTheDocument()
})
