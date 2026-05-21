/**
 * Profile 03 — Stress: Find Max Capacity
 *
 * Purpose: Empirically find where the system breaks.
 *          Steps browse VUs from 50 → 1500.
 *          AI rates stay FIXED (not scaled with VUs) to protect OpenAI budget.
 *          abortOnFail: false so we record the exact breaking step.
 *
 * Answers Q2: at what VU count does error rate exceed 1% or p95 exceed 2s?
 *
 * Estimated OpenAI cost: ~$8
 * Expected duration: ~35 minutes
 *
 * Run:
 *   k6 cloud load_tests/profiles/03_stress_ramp.js
 *
 * After run: record which VU step first caused threshold breaches.
 */

import { browseDashboard, browseFlashcards, triggerAIHelp, startVoiceSession } from '../lib/scenarios.js';
import { getUser } from '../lib/users.js';
import { sleep } from 'k6';

export const options = {
  cloud: {
    projectID: 7601757,
    name: '03_stress_ramp',
    distribution: {
      frankfurt: { loadZone: 'amazon:de:frankfurt', percent: 100 },
    },
  },
  scenarios: {
    // Browse VUs step up through capacity bands
    browse_scenario: {
      executor: 'ramping-vus',
      startVUs: 0,
      // 75 browse VUs max (+ 15 ai_help + 10 realtime = 100 total, at project limit)
      // Steps find the breaking point within the full available budget
      stages: [
        { duration: '30s', target: 10 },    // step 1: 10 VUs
        { duration: '4m30s', target: 10 },
        { duration: '30s', target: 25 },    // step 2: 25 VUs
        { duration: '4m30s', target: 25 },
        { duration: '30s', target: 40 },    // step 3: 40 VUs
        { duration: '4m30s', target: 40 },
        { duration: '30s', target: 55 },    // step 4: 55 VUs
        { duration: '4m30s', target: 55 },
        { duration: '30s', target: 65 },    // step 5: 65 VUs
        { duration: '4m30s', target: 65 },
        { duration: '30s', target: 75 },    // step 6: 75 VUs (full budget)
        { duration: '4m30s', target: 75 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'browseFn',
    },
    // AI rates are FIXED — same as profile 02, not scaled
    ai_help_scenario: {
      executor: 'constant-arrival-rate',
      rate: 3,          // reduced from 5 to prevent VU starvation on slow AI calls
      timeUnit: '1s',
      duration: '33m',
      preAllocatedVUs: 15,
      maxVUs: 15,
      startTime: '30s',
      exec: 'aiHelpFn',
    },
    realtime_scenario: {
      executor: 'constant-arrival-rate',
      rate: 2,
      timeUnit: '1s',
      duration: '33m',
      preAllocatedVUs: 10,
      maxVUs: 10,
      startTime: '30s',
      exec: 'realtimeFn',
    },
  },
  thresholds: {
    // abortOnFail: false — let all steps run so we know exactly where it breaks
    'http_req_duration{endpoint:browse}': [
      { threshold: 'p(95)<500', abortOnFail: false },
      { threshold: 'p(95)<2000', abortOnFail: false },   // hard ceiling
    ],
    'http_req_duration{endpoint:flashcards}': [
      { threshold: 'p(95)<500', abortOnFail: false },
    ],
    'http_req_duration{endpoint:ai_help}': [
      { threshold: 'p(95)<3000', abortOnFail: false },
    ],
    'http_req_duration{endpoint:realtime_token}': [
      { threshold: 'p(95)<1000', abortOnFail: false },
    ],
    'http_req_failed': [
      { threshold: 'rate<0.01', abortOnFail: false },
      { threshold: 'rate<0.05', abortOnFail: false },     // hard ceiling
    ],
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
