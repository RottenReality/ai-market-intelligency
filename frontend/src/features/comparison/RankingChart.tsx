import { Bar, BarChart, LabelList, XAxis, YAxis } from 'recharts'
import { SERIES_COLORS } from '@/lib/colors'
import type { ComparedCountry } from '@/lib/types'

export function RankingChart({ countries }: { countries: ComparedCountry[] }) {
  const data = countries
    .filter((c) => c.accessibility !== null)
    .map((c) => ({ name: c.name, value: Math.round(c.accessibility as number) }))
  if (data.length === 0) return null

  return (
    <BarChart
      width={560}
      height={48 * data.length + 40}
      data={data}
      layout="vertical"
      margin={{ top: 8, right: 48, bottom: 8, left: 8 }}
    >
      <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
      <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 13 }} />
      <Bar dataKey="value" fill={SERIES_COLORS[0]} radius={[0, 4, 4, 0]} barSize={22}>
        <LabelList dataKey="value" position="right" formatter={(v) => `${v}%`} />
      </Bar>
    </BarChart>
  )
}
