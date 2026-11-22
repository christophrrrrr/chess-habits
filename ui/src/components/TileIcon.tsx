import {
  AlarmClock,
  BookOpen,
  Coffee,
  FastForward,
  ListChecks,
  ChartColumn,
  Crown,
  Hourglass,
  ListOrdered,
  OctagonX,
  RotateCcw,
  ScanEye,
  Swords,
  Sunrise,
  Target,
  TrendingUp,
  type LucideIcon,
} from 'lucide-react'
import { createElement } from 'react'

const ICONS: Record<string, LucideIcon> = {
  clock_profile: Hourglass,
  time_trouble_score: AlarmClock,
  after_loss_requeue: RotateCcw,
  after_loss_result: Swords,
  stop_loss_rules: OctagonX,
  rule: Target,
  games: ListOrdered,
  grandmaster: Crown,
  gaze: ScanEye,
  warm_up: Coffee,
  time_of_day: Sunrise,
  opening_time: BookOpen,
  premoves: FastForward,
  form: TrendingUp,
  plan: ListChecks,
}

/** The icon for an analysis key (or "rule", "games", ...); a chart for anything new. */
export function TileIcon({ name, size = 22 }: { name: string; size?: number }) {
  return createElement(ICONS[name] ?? ChartColumn, { size, 'aria-hidden': true })
}
