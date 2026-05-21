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
      // Steps capped at 70 browse VUs (+ 20 ai + 10 realtime = 100 total limit)
      // Steps find the breaking point within available VU budget
      stages: [
        { duration: '30s', target: 10 },    // step 1: 10 VUs
        { duration: '4m30s', target: 10 },
        { duration: '30s', target: 20 },    // step 2: 20 VUs
        { duration: '4m30s', target: 20 },
        { duration: '30s', target: 35 },    // step 3: 35 VUs
        { duration: '4m30s', target: 35 },
        { duration: '30s', target: 50 },    // step 4: 50 VUs
        { duration: '4m30s', target: 50 },
        { duration: '30s', target: 60 },    // step 5: 60 VUs
        { duration: '4m30s', target: 60 },
        { duration: '30s', target: 70 },    // step 6: 70 VUs (max allowed)
        { duration: '4m30s', target: 70 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'browseFn',
    },
    // AI rates are FIXED — same as profile 02, not scaled
    ai_help_scenario: {
      executor: 'constant-arrival-rate',
      rate: 5,
      timeUnit: '1s',
      duration: '33m',
      preAllocatedVUs: 20,
      maxVUs: 20,
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
