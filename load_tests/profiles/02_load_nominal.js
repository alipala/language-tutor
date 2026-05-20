/**
 * Profile 02 — Load: Nominal Capacity
 *
 * Purpose: Validate the "nominal capacity" claim at 200 concurrent users.
 *          Answers Q1: at what VU count does p95 breach 500ms for browse
 *          and 3000ms for AI endpoints?
 *
 * Estimated OpenAI cost: ~$2
 * Expected duration: ~22 minutes
 *
 * Run:
 *   k6 cloud load_tests/profiles/02_load_nominal.js
 *
 * GO/NO-GO: all thresholds green + Railway metrics healthy → proceed to 03
 */

import { browseDashboard, browseFlashcards, triggerAIHelp, startVoiceSession } from '../lib/scenarios.js';
import { getUser } from '../lib/users.js';
import { sleep } from 'k6';

export const options = {
  cloud: {
    projectID: 7601757,
    name: '02_load_nominal',
    distribution: {
      frankfurt: { loadZone: 'amazon:de:frankfurt', percent: 100 },
    },
  },
  scenarios: {
    // Main browse traffic: ramps to 200 VUs and holds
    browse_scenario: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 200 },   // ramp up
        { duration: '15m', target: 200 },  // steady state
        { duration: '2m', target: 0 },     // ramp down
      ],
      gracefulRampDown: '30s',
      exec: 'browseFn',
    },
    // AI help: fixed arrival rate (5 req/s) — independent of VU count
    ai_help_scenario: {
      executor: 'constant-arrival-rate',
      rate: 5,
      timeUnit: '1s',
      duration: '19m',
      preAllocatedVUs: 20,
      maxVUs: 40,
      startTime: '2m',   // start when browse VUs are at steady state
      exec: 'aiHelpFn',
    },
    // Realtime token: fixed arrival rate (2 req/s)
    realtime_scenario: {
      executor: 'constant-arrival-rate',
      rate: 2,
      timeUnit: '1s',
      duration: '19m',
      preAllocatedVUs: 10,
      maxVUs: 20,
      startTime: '2m',
      exec: 'realtimeFn',
    },
  },
  thresholds: {
    'http_req_duration{endpoint:browse}':          ['p(95)<500'],
    'http_req_duration{endpoint:flashcards}':       ['p(95)<500'],
    'http_req_duration{endpoint:ai_help}':          ['p(95)<3000'],
    'http_req_duration{endpoint:realtime_token}':   ['p(95)<1000'],
    'http_req_failed':                              ['rate<0.01'],
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
