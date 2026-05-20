/**
 * Profile 01 — Smoke Test
 *
 * Purpose: Catch obvious breakage before running larger tests.
 *          1 VU, 1 minute, non-AI endpoints only.
 *
 * Estimated OpenAI cost: $0
 * Expected duration: ~1 minute
 *
 * Run:
 *   k6 cloud load_tests/profiles/01_smoke.js
 *
 * GO/NO-GO: all thresholds green → proceed to profile 02
 */

import { browseDashboard, browseFlashcards } from '../lib/scenarios.js';
import { getUser } from '../lib/users.js';

export const options = {
  cloud: {
    projectID: 7601757,
    name: '01_smoke',
    distribution: {
      frankfurt: { loadZone: 'amazon:de:frankfurt', percent: 100 },
    },
  },
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '1m',
      exec: 'smokeFn',
    },
  },
  thresholds: {
    'http_req_duration{endpoint:browse}':      ['p(95)<300'],
    'http_req_duration{endpoint:flashcards}':   ['p(95)<300'],
    'http_req_failed':                          ['rate<0.001'],
  },
};

export function smokeFn() {
  const { jwt } = getUser(__VU);
  browseDashboard(jwt);
  browseFlashcards(jwt);
}
