import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { IndustryGrid } from '../IndustryGrid'
import type { IndustrySummary } from '@/types/api'
import type { ReactNode } from 'react'

// Mock recharts — jsdom cannot render SVG meaningfully.
// The mock renders a plain div so @testing-library/react can find elements.
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => <>{children}</>,
  BarChart: ({
    children,
    onClick,
  }: {
    children: ReactNode
    onClick?: React.MouseEventHandler
  }) => (
    <div data-testid="bar-chart" onClick={onClick}>
      {children}
    </div>
  ),
  Bar: ({ children }: { children?: ReactNode }) => <>{children}</>,
  Cell: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}))

const MOCK_DATA: IndustrySummary[] = [
  { industry: 'Fintech', jobCount: 30, scoredCount: 10, avgScore: 72.5 },
  { industry: 'CleanTech', jobCount: 25, scoredCount: 8, avgScore: 41.3 },
  { industry: 'HealthTech', jobCount: 20, scoredCount: 0, avgScore: null },
]

describe('IndustryGrid', () => {
  it('renders an accessible label for every industry in the data', () => {
    render(<IndustryGrid data={MOCK_DATA} selectedIndustry={null} onSelect={() => {}} />)

    for (const { industry } of MOCK_DATA) {
      expect(screen.getByTestId(`industry-label-${industry}`)).toBeInTheDocument()
    }
  })

  it('shows the correct job count in each label', () => {
    render(<IndustryGrid data={MOCK_DATA} selectedIndustry={null} onSelect={() => {}} />)

    expect(screen.getByTestId('industry-label-Fintech')).toHaveTextContent('30 jobs')
    expect(screen.getByTestId('industry-label-CleanTech')).toHaveTextContent('25 jobs')
    expect(screen.getByTestId('industry-label-HealthTech')).toHaveTextContent('20 jobs')
  })

  it('includes the avg score in the label when the industry has been scored', () => {
    render(<IndustryGrid data={MOCK_DATA} selectedIndustry={null} onSelect={() => {}} />)

    expect(screen.getByTestId('industry-label-Fintech')).toHaveTextContent('72.5')
    expect(screen.getByTestId('industry-label-CleanTech')).toHaveTextContent('41.3')
  })

  it('omits score text for industries that have not been scored yet', () => {
    render(<IndustryGrid data={MOCK_DATA} selectedIndustry={null} onSelect={() => {}} />)

    const label = screen.getByTestId('industry-label-HealthTech')
    expect(label).not.toHaveTextContent('score')
    expect(label).not.toHaveTextContent('avg')
  })

  it('renders the recharts bar chart container', () => {
    render(<IndustryGrid data={MOCK_DATA} selectedIndustry={null} onSelect={() => {}} />)

    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('renders without crashing when passed an empty dataset', () => {
    expect(() =>
      render(<IndustryGrid data={[]} selectedIndustry={null} onSelect={() => {}} />)
    ).not.toThrow()
  })

  it('renders all three legend items', () => {
    render(<IndustryGrid data={MOCK_DATA} selectedIndustry={null} onSelect={() => {}} />)

    expect(screen.getByText(/Low risk/)).toBeInTheDocument()
    expect(screen.getByText(/Moderate/)).toBeInTheDocument()
    expect(screen.getByText(/High risk/)).toBeInTheDocument()
    expect(screen.getByText(/Not scored/)).toBeInTheDocument()
  })
})
