import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatRaw, formatScore } from '@/lib/format'
import type { IndicatorResult } from '@/lib/types'

export function IndicatorTable({ indicators }: { indicators: IndicatorResult[] }) {
  return (
    <Table className="table-fixed">
      <TableHeader>
        <TableRow>
          <TableHead className="w-[38%]">Indicator</TableHead>
          <TableHead className="w-[14%] text-right">Raw value</TableHead>
          <TableHead className="w-[10%] text-right">Score</TableHead>
          <TableHead className="w-[38%] pl-6">Source</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {indicators.map((indicator) => (
          <TableRow key={indicator.id}>
            <TableCell className="whitespace-normal">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{indicator.id}</Badge>
                <span>{indicator.name}</span>
              </div>
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatRaw(indicator.raw, indicator.unit)}
            </TableCell>
            <TableCell className="text-right font-medium tabular-nums">
              {formatScore(indicator.score)}
            </TableCell>
            <TableCell className="pl-6 whitespace-normal">
              <div className="flex flex-col gap-0.5">
                {indicator.sources.map((source) => (
                  <a
                    key={source.url}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-primary underline-offset-4 hover:underline"
                  >
                    {source.name}
                    {source.year ? ` (${source.year})` : ''}
                  </a>
                ))}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
