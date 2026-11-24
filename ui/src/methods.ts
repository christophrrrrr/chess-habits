// What the methods page shows: every definition and threshold the analyses use, written for
// players. docs/definitions.md is the source; keep the two in sync when a threshold changes.

export interface MethodsEntry {
  term: string
  text: string
}

export interface MethodsSection {
  id: string
  title: string
  intro: string
  entries: MethodsEntry[]
}

export const METHODS: MethodsSection[] = [
  {
    id: 'games',
    title: 'Games and sessions',
    intro: 'Which games count, and how games are grouped into sessions.',
    entries: [
      {
        term: 'Time control',
        text: 'chess.com’s bullet, blitz and rapid, except that live games with an estimated game time of 25 minutes or more count as classical. Daily games are never analysed.',
      },
      {
        term: 'Estimated game time',
        text: 'Base time plus 40 times the increment, per player. A 10+5 game is 10 min + 40 × 5 s = 13 min 20 s.',
      },
      {
        term: 'Time spent on a move',
        text: 'Your clock before the move, plus the increment, minus your clock after the move.',
      },
      {
        term: 'Session',
        text: 'Games in a row where the next game starts at most 30 minutes after the previous one ended.',
      },
      {
        term: 'Quick requeue',
        text: 'Starting the next game within 60 seconds of the previous game’s end.',
      },
      {
        term: 'Final material',
        text: 'Your material minus your opponent’s in the final position (pawn 1, knight and bishop 3, rook 5, queen 9). Winning means at least +3, losing at most −3, anything else is level. It misses some winning positions but is rarely wrong when it says winning.',
      },
    ],
  },
  {
    id: 'results',
    title: 'Ratings and results',
    intro:
      'Every result finding compares how you scored with how you were expected to score, so a habit is not confused with playing stronger or weaker opponents.',
    entries: [
      {
        term: 'Your strength',
        text: 'The median of your ratings over the 25 games before and after a game, in the same time control.',
      },
      {
        term: 'Expected score',
        text: 'The Elo formula with your strength against your opponent’s rating before the game.',
      },
      {
        term: 'Residual',
        text: 'Your actual score (1 for a win, ½ for a draw, 0 for a loss) minus the expected score.',
      },
      {
        term: 'Elo equivalent',
        text: 'A difference in score turned into rating points: about 695 Elo per full point of score.',
      },
    ],
  },
  {
    id: 'clock',
    title: 'Clock profile',
    intro: 'How and when you get into time trouble.',
    entries: [
      {
        term: 'Time trouble',
        text: 'Your clock drops below 10% of the estimated game time and you still make at least 5 more moves, so a quick mate in time trouble does not count. Games need at least 10 of your moves with clock data.',
      },
      { term: 'Scramble', text: 'The same, with 3% instead of 10%.' },
      { term: 'Onset move', text: 'Your first move in time trouble.' },
      {
        term: 'Self-inflicted',
        text: 'At the onset move, your opponent had more time left than you.',
      },
      {
        term: 'Where the time went',
        text: 'Your thinking time before the onset, split into opening (moves 2 to 12), spikes (single moves of at least 4 times your usual think time, moves 13 to 40) and drain (the rest), compared with calm games. Shown from 30 games with time trouble.',
      },
      {
        term: 'Pace',
        text: 'Median share of your clock left after moves 10, 20, 30 and 40, in wins and in losses (from 10 games per cell).',
      },
      {
        term: 'Net clock points',
        text: 'Points you win on time from losing or level positions minus points you lose on time from winning or level positions, per 100 games.',
      },
    ],
  },
  {
    id: 'statistics',
    title: 'Statistics and labels',
    intro: 'When a card makes a claim, and how sure it is.',
    entries: [
      {
        term: 'Interval',
        text: 'A 95% interval from 2,000 bootstrap resamples. Games from the same session are resampled together when the question is about games in a row.',
      },
      {
        term: 'Finding',
        text: 'The effect is clear after correcting for testing many things at once (Benjamini–Hochberg, q ≤ 0.05).',
      },
      { term: 'Exploratory', text: 'A weaker signal (q ≤ 0.10): worth watching, not a conclusion.' },
      {
        term: 'No clear effect',
        text: 'Nothing larger than the smallest effect your games could detect (2.8 times the standard error). It does not prove there is no effect at all.',
      },
      {
        term: 'Not enough data',
        text: 'Fewer than 100 games in the smaller group for score findings, or fewer than 30 for behaviour rates. No claim is made. A time control with fewer than 20 games gets no cards.',
      },
      { term: 'Early estimate', text: 'A clock profile from fewer than 100 games.' },
    ],
  },
  {
    id: 'rules',
    title: 'Rules',
    intro: 'Suggestions you adopt, and how Chess Habits checks whether you keep them.',
    entries: [
      {
        term: 'Rule',
        text: 'A clock checkpoint or a stop-loss rule you adopted from a card, per time control. At most one of each kind per time control.',
      },
      {
        term: 'Clock checkpoint',
        text: '“Keep at least X of your clock after move 20.” A game that reaches move 20 keeps it if your clock after that move is at least X of the estimated game time.',
      },
      {
        term: 'Suggested X',
        text: 'A floor that 3 in 4 of your wins clear, rounded down to 5%, at least 5%. Needs 30 wins that reached move 20.',
      },
      {
        term: 'Stop-loss rule',
        text: '“Stop after 2 losses in a row”, “3 in a row” or “3 losses in one session”. A session where the rule said stop keeps it if you played no more games of that time control.',
      },
      {
        term: 'Helps or costs',
        text: 'A stop-loss rule helps if the games it would have skipped went clearly worse than your other games, and costs if they went clearly better. Needs 30 skipped games.',
      },
      {
        term: 'Baseline',
        text: 'Your last 300 games or sessions before you adopted the rule, scored as if the rule had applied.',
      },
      {
        term: 'Rule verdict',
        text: 'How often you keep the rule since adopting it compared with the baseline. Too early until there are 30 games or sessions on both sides. It is a before and after comparison, not a controlled experiment.',
      },
      { term: 'Changing a rule', text: 'Changing the threshold starts the count again.' },
    ],
  },
  {
    id: 'habits',
    title: 'More habits',
    intro:
      'Warm-up, time of day, opening time, premoves and form. All from the clock and the results you already import.',
    entries: [
      {
        term: 'First game of a session',
        text: 'Your score against expectation in the first game after a break of more than 30 minutes, compared with later games in the same sessions. Needs 100 games on each side.',
      },
      {
        term: 'Time of day',
        text: 'Your score against expectation for games you start at night (0–6 h), in the morning (6–12 h), afternoon (12–18 h) and evening (18–24 h), in your browser’s time zone. A window counts as clearly different only if it beats the rest after a Bonferroni correction for four windows, with at least 100 games inside and outside it.',
      },
      {
        term: 'Opening time',
        text: 'Share of the estimated game time used by your move 12, overall and for each opening you played at least 20 times (chess.com’s opening name shortened to its family, e.g. Caro Kann Defense; broad families such as Queens Pawn Opening keep their next named part). Each opening’s score is shown with a 95% interval; openings are compared one by one, so a single result is a hint.',
      },
      {
        term: 'Premove',
        text: 'A move that took exactly 0.1 s, which is what chess.com charges for a premove. Shown only in bullet and blitz, and only if 0.1 s moves are at least 3 times as common as 0.2 s moves (otherwise you do not premove).',
      },
      {
        term: 'Form over time',
        text: 'Per month: games played, the median of your ratings, and your score against expectation from 10 games.',
      },
      {
        term: 'Your plan',
        text: 'Every habit with clear evidence, ranked by Elo over an average game: the cost in the games it affects times the share of games it affects. For example, time trouble that costs 100 Elo in 20% of your games ranks as about 20 Elo per game.',
      },
    ],
  },
  {
    id: 'deep',
    title: 'Deep analysis (Stockfish)',
    intro:
      'Stockfish 19 (lite) runs in your browser on your own positions; the results are stored with your account.',
    entries: [
      {
        term: 'Engine pass',
        text: 'Every position before one of your moves in your most recent games is searched with 100,000 nodes for the two best moves (MultiPV 2). Evaluations become win% with the Lichess curve.',
      },
      {
        term: 'Critical moment',
        text: 'A position that is not decided yet (best move 10–95% win) where the second-best move already loses 10+ win% points. Recaptures, positions where you are in check and positions with 3 legal moves or fewer are left out, because those moves are obvious.',
      },
      {
        term: 'Found',
        text: 'You played the best move or one that loses less than 3 win% points.',
      },
      {
        term: 'Kind of move',
        text: 'Check, capture, castling, king move, pawn move, retreat (a piece moves back towards your side) or quiet move, for the best move.',
      },
      {
        term: 'Resigned too early',
        text: 'You resigned with at least 15% expected score left, by the engine’s evaluation of the final position (also shown for 10% and 25%). Compared with how your opponents resign against you. The curve ignores the clock, so resigning with seconds left can still be sensible.',
      },
      {
        term: 'Lost on time while winning',
        text: 'The engine has you 3+ pawns ahead in the final position of a game lost on time.',
      },
      {
        term: 'Opening autopilot',
        text: 'A position counts as known when you reached exactly the same position (pieces, side to move, castling, en passant) 3+ times in earlier games of the same time control. Compares your time per move in known and new positions over your first 20 moves.',
      },
    ],
  },
  {
    id: 'compare',
    title: 'Grandmaster comparison',
    intro: 'Your habits next to a grandmaster’s.',
    entries: [
      {
        term: 'Grandmaster',
        text: 'A chess.com account imported and analysed exactly like yours, from its last 12 months of games.',
      },
      {
        term: 'Comparison',
        text: 'Your latest analysis next to the grandmaster’s, for every time control you both play. Nothing is recomputed.',
      },
      {
        term: 'Difference of shares',
        text: 'For time trouble, scramble and self-inflicted: you minus the grandmaster, with a 95% interval. Needs 30 games on both sides.',
      },
      {
        term: 'Difference of effects',
        text: 'For the Elo rows: you minus the grandmaster, only when both sides have enough data for their own card. Each side is measured against its own expected results, so this compares habits, not strength.',
      },
      {
        term: 'Verdict',
        text: 'Clearly different (q ≤ 0.05), maybe different (q ≤ 0.10) or no clear difference, after correcting for testing every row at once. Onset move and clock at move 20 are shown but not tested.',
      },
    ],
  },
]

/** The section that explains each analysis; anything new falls back to the statistics. */
const SECTION_FOR_ANALYSIS: Record<string, string> = {
  clock_profile: 'clock',
  time_trouble_score: 'clock',
  after_loss_requeue: 'games',
  after_loss_result: 'results',
  stop_loss_rules: 'rules',
  rule_check: 'rules',
  warm_up: 'habits',
  time_of_day: 'habits',
  opening_time: 'habits',
  premoves: 'habits',
  form: 'habits',
  critical_moments: 'deep',
  endings: 'deep',
  opening_autopilot: 'deep',
}

export function methodsSectionFor(analysisKey: string): string {
  return SECTION_FOR_ANALYSIS[analysisKey] ?? 'statistics'
}
