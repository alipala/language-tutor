/**
 * Profile 05 — Soak: Sustained Stability (1 hour)
 *
 * Purpose: Detect memory leaks, connection pool exhaustion, or slow
 *          p95 degradation over sustained load.
 *          Answers Q4: across 1 hour at nominal capacity, are there
 *          memory leaks or degradation?
 *
 * Pattern: 150 VUs constant for 60 minutes. AI rates reduced to save budget.
 *
 * Degradation check (manual from Grafana):
 *   - Capture p95 for browse in minutes 0–5.
 *   - Capture p95 for browse in minutes 55–60.
 *   - Threshold: final p95 must be ≤ 120% of initial p95.
 *
 * Estimated OpenAI cost: ~$5
 * Expected duration: ~65 minutes
 *
 * Run:
 *   k6 cloud load_tests/profiles/05_soak.js
 *
 * During run: watch Railway Metrics → Memory for upward trend.
 */

import { browseDashboard, browseFlashcards, triggerAIHelp, startVoiceSession } from '../lib/scenarios.js';
import { getUser } from '../lib/users.js';
import { sleep } from 'k6';

export const options = {
  cloud: {
    projectID: 7601757,
    name: '05_soak',
    distribution: {
      frankfurt: { loadZone: 'amazon:de:frankfurt', percent: 100 },
    },
  },
  scenarios: {
    browse_scenario: {
      executor: 'ramping-vus',
      startVUs: 0,
      // 70 VUs max (+ 15 ai + 5 realtime = 90 total, under 100 limit)
      stages: [
        { duration: '2m', target: 70 },    // ramp up
        { duration: '60m', target: 70 },   // 1-hour soak
        { duration: '2m', target: 0 },     // ramp down
      ],
      gracefulRampDown: '30s',
      exec: 'browseFn',
    },
    // Reduced AI rates vs profiles 02/03 to stay within budget
    ai_help_scenario: {
      executor: 'constant-arrival-rate',
      rate: 3,           // 3/sec (vs 5/sec in other profiles)
      timeUnit: '1s',
      duration: '62m',
      preAllocatedVUs: 15,
      maxVUs: 30,
      startTime: '2m',
      exec: 'aiHelpFn',
    },
    realtime_scenario: {
      executor: 'constant-arrival-rate',
      rate: 1,           // 1/sec (vs 2/sec in other profiles)
      timeUnit: '1s',
      duration: '62m',
      preAllocatedVUs: 5,
      maxVUs: 15,
      startTime: '2m',
      exec: 'realtimeFn',
    },
  },
  thresholds: {
    // Stricter error rate than spike profile — soak should be clean
    'http_req_duration{endpoint:browse}':        ['p(95)<500'],
    'http_req_duration{endpoint:flashcards}':     ['p(95)<500'],
    'http_req_duration{endpoint:ai_help}':        ['p(95)<3000'],
    'http_req_duration{endpoint:realtime_token}': ['p(95)<1000'],
    'http_req_failed':                            ['rate<0.005'],
  },
};

export function browseFn() {
  const { jwt } = getUser(__VU);
  browseDashboard(jwt);
  browseFlashcards(jwt);
}

export function aiHelpFn() {
  const { jwt } = getUser(__VU);
  triggerAIHelp(jwt);
  sleep(1);
}

export function realtimeFn() {
  const { jwt } = getUser(__VU);
  startVoiceSession(jwt);
  sleep(3);
}
