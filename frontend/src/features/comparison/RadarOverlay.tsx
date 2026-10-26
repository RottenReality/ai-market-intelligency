import { Legend, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart } from 'recharts'
import { MAX_RADAR_SERIES, SERIES_COLORS } from '@/lib/colors'
import type { ComparedCountry, DimensionId } from '@/lib/types'

const DIMENSIONS: [DimensionId, string][] = [
  ['C', 'Cultural'],
  ['A', 'Administrative'],
  ['G', 'Geographic'],
  ['E', 'Economic'],
]

export function RadarOverlay({ countries }: { countries: ComparedCountry[] }) {
  const shown = countries.slice(0, MAX_RADAR_SERIES)
  const data = DIMENSIONS.map(([id, name]) => ({
    name,
    ...Object.fromEntries(shown.map((c) => [c.iso3, c.dimensions[id] ?? 0])),
  }))

  return (
    <div className="shrink-0" style={{ width: 420, height: 340 }}>
      <RadarChart
        width={420}
        height={340}
        data={data}
        outerRadius={110}
        margin={{ top: 16, right: 72, bottom: 16, left: 64 }}
      >
        <PolarGrid />
        <PolarAngleAxis dataKey="name" tick={{ fontSize: 13, fill: 'currentColor' }} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        {shown.map((country, index) => (
          <Radar
            key={country.iso3}
            name={country.name}
            dataKey={country.iso3}
            stroke={SERIES_COLORS[index]}
            fill={SERIES_COLORS[index]}
            fillOpacity={0.1}
            strokeWidth={2}
          />
        ))}
        <Legend />
      </RadarChart>
    </div>
  )
}
