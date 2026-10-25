import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, Tooltip } from 'recharts'
import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table'
import { SERIES_COLORS } from '@/lib/colors'
import { formatScore } from '@/lib/format'
import type { Dimension } from '@/lib/types'

export function DimensionRadar({ dimensions }: { dimensions: Dimension[] }) {
  const data = dimensions.map((d) => ({
    name: d.name,
    score: d.score ?? 0,
    hasData: d.score !== null,
  }))

  return (
    <div className="flex flex-col items-center gap-2 sm:flex-row sm:items-start">
      <div className="shrink-0" style={{ width: 400, height: 300 }}>
        <RadarChart
        width={400}
        height={300}
        data={data}
        outerRadius={100}
        margin={{ top: 16, right: 72, bottom: 16, left: 64 }}
      >
        <PolarGrid />
        <PolarAngleAxis dataKey="name" tick={{ fontSize: 13, fill: 'currentColor' }} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        <Tooltip
          formatter={(value, _name, item) =>
            item.payload.hasData ? `${Math.round(Number(value))}%` : 'no data'
          }
        />
        <Radar
          name="Dimension score"
          dataKey="score"
          stroke={SERIES_COLORS[0]}
          fill={SERIES_COLORS[0]}
          fillOpacity={0.15}
          strokeWidth={2}
        />
        </RadarChart>
      </div>
      <Table className="w-auto">
        <TableBody>
          {dimensions.map((d) => (
            <TableRow key={d.id}>
              <TableCell className="font-medium">{d.name}</TableCell>
              <TableCell className="text-right tabular-nums">{formatScore(d.score)}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {d.available}/{d.total} indicators
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
