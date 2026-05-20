/**
 * Profile 04 — Spike Resilience
 *
 * Purpose: Prove no cascading failure on a 5× sudden traffic burst.
 *          Answers Q3: does the system survive and recover within 60 seconds?
 *
 * Pattern:
 *   30s  → ramp to 100 VUs  (baseline)
 *   3m   → hold 100 VUs
 *   30s  → spike to 800 VUs (8× burst)
 *   90s  → hold spike
 *   30s  → drop back to 100 VUs
 *   5m   → recover at 100 VUs (watch p95 return to baseline)
 *
 * Recovery criterion: p95 in last 2 minutes ≤ 2× p95 in pre-spike 3 minutes.
 * (Verified manually from Grafana timeseries — no k6 built-in for this.)
 *
 * Estimated OpenAI cost: ~$3
 * Expected duration: ~11 minutes
 *
 * Run:
 *   k6 cloud load_tests/profiles/04_spike.js
 */

import { browseDashboard, browseFlashcards, triggerAIHelp, startVoiceSession } from '../lib/scenarios.js';
import { getUser } from '../lib/users.js';
import { sleep } from 'k6';

export const options = {
  cloud: {
    projectID: 7601757,
    name: '04_spike',
    distribution: {
      frankfurt: { loadZone: 'amazon:de:frankfurt', percent: 100 },
    },
  },
  scenarios: {
    browse_scenario: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 100 },   // baseline ramp
        { duration: '3m', target: 100 },    // pre-spike steady state
        { duration: '30s', target: 800 },   // instant spike
        { duration: '90s', target: 800 },   // spike hold
        { duration: '30s', target: 100 },   // drop back
        { duration: '5m', target: 100 },    // recovery observation window
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'browseFn',
    },
    // AI rates: same fixed caps as other profiles
    ai_help_scenario: {
      executor: 'constant-arrival-rate',
      rate: 5,
      timeUnit: '1s',
      duration: '10m',
      preAllocatedVUs: 20,
      maxVUs: 40,
      startTime: '30s',
      exec: 'aiHelpFn',
    },
    realtime_scenario: {
      executor: 'constant-arrival-rate',
      rate: 2,
      timeUnit: '1s',
      duration: '10m',
      preAllocatedVUs: 10,
      maxVUs: 20,
      startTime: '30s',
      exec: 'realtimeFn',
    },
  },
  thresholds: {
    // Spike-tolerant: allow higher p95 and error rate during the burst
    'http_req_duration{endpoint:browse}':        ['p(95)<2000'],
    'http_req_duration{endpoint:flashcards}':     ['p(95)<2000'],
    'http_req_duration{endpoint:ai_help}':        ['p(95)<5000'],
    'http_req_duration{endpoint:realtime_token}': ['p(95)<3000'],
    'http_req_failed':                            ['rate<0.05'],   // 5% acceptable during spike
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
  sleep(2);
}
