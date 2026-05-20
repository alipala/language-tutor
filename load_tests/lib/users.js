/**
 * Load-test user pool — shared k6 library.
 *
 * Reads users from the bundled data/users.json file (included automatically
 * by k6 cloud when you run `k6 cloud run` from the load_tests/ directory).
 *
 * No Grafana environment variable needed — k6 bundles the file at upload time.
 *
 * Usage:
 *   import { getUser } from '../lib/users.js';
 *   const user = getUser(__VU);   // {user_id, email, jwt}
 */

import { SharedArray } from 'k6/data';

const _pool = new SharedArray('loadTestUsers', function () {
  const raw = open('../data/users.json');
  return JSON.parse(raw).users;
});

if (!_pool || _pool.length === 0) {
  throw new Error('[users.js] data/users.json loaded but contains no users.');
}

/**
 * Returns the load-test user assigned to this VU.
 * Assignment is stable across iterations: VU N always gets user (N-1) % poolSize.
 *
 * @param {number} vuId  k6 __VU (1-indexed)
 * @returns {{ user_id: string, email: string, jwt: string }}
 */
export function getUser(vuId) {
  const idx = (vuId - 1) % _pool.length;
  return _pool[idx];
}

/** Total number of users in the pool. */
export const poolSize = _pool.length;
