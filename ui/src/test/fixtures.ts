import type { Finding } from '../api'

export const contrast: Finding = {
  id: 1,
  analysis_key: 'time_trouble_score',
  time_class: 'bullet',
  kind: 'contrast',
  metric: 'score',
  label: 'finding',
  title: 'Bullet: time trouble costs you about 110 Elo',
  summary: 'In bullet, you score -17.8 points against expectation in games with time trouble.',
  effect: -0.158,
  ci_low: -0.236,
  ci_high: -0.072,
  mde: 0.12,
  p_value: 0.001,
  sample_size: 828,
  details: {},
}

export const clockProfile: Finding = {
  id: 2,
  analysis_key: 'clock_profile',
  time_class: 'bullet',
  kind: 'profile',
  metric: 'profile',
  label: 'profile',
  title: 'Bullet: time trouble in 19% of games, mostly self-inflicted',
  summary: 'Your clock drops below 10% of the expected game time.',
  effect: null,
  ci_low: null,
  ci_high: null,
  mde: null,
  p_value: null,
  sample_size: 828,
  details: {
    games_with_clock: 828,
    early_estimate: false,
    entry: { count: 155, n: 828, rate: 0.187, ci: [0.16, 0.21] },
    scramble: { count: 80, n: 828, rate: 0.1, ci: [0.08, 0.12] },
    onset_move: { median: 40, iqr: [33, 48] },
    self_inflicted: { count: 119, n: 155, rate: 0.77, ci: [0.7, 0.83] },
    time_sinks: { entry_games: 155, main_cause_share: { opening: 0.05, spikes: 0.28, drain: 0.67 } },
    pace: {
      wins: { '10': 0.85, '20': 0.56, '30': 0.3, '40': 0.17 },
      losses: { '10': 0.84, '20': 0.52, '30': 0.22, '40': null },
    },
    flags: {
      lost_on_time: { winning: 45, level: 93, losing: 86, unknown: 0 },
      won_on_time: { winning: 87, level: 56, losing: 31, unknown: 0 },
      net_points_per_100: -3.8,
    },
  },
}

export const stopLoss: Finding = {
  id: 3,
  analysis_key: 'stop_loss_rules',
  time_class: 'bullet',
  kind: 'profile',
  metric: 'profile',
  label: 'profile',
  title: 'Bullet: a stop-loss rule would not have helped you',
  summary: 'None of the common stop-loss rules would have skipped games you played below your level.',
  effect: null,
  ci_low: null,
  ci_high: null,
  mde: null,
  p_value: null,
  sample_size: 800,
  details: {
    rules: [
      {
        rule: 'two_in_a_row',
        name: 'Stop after 2 losses in a row',
        skipped_games: 585,
        difference_elo: 69,
        ci_elo: [20, 118],
        verdict: 'costs',
      },
      {
        rule: 'three_in_session',
        name: 'Stop after 3 losses in one session',
        skipped_games: 0,
        difference_elo: null,
        ci_elo: null,
        verdict: 'not_enough_data',
      },
    ],
  },
}

export const requeue: Finding = {
  ...contrast,
  id: 4,
  analysis_key: 'after_loss_requeue',
  metric: 'share',
  title: 'Rapid: you requeue faster after a loss',
  time_class: 'rapid',
  effect: 0.107,
  ci_low: 0.055,
  ci_high: 0.157,
}

export const notEnough: Finding = {
  ...contrast,
  id: 5,
  analysis_key: 'after_loss_result',
  label: 'not_enough_data',
  title: 'Classical: not enough games to judge your play right after a loss',
  time_class: 'classical',
}
