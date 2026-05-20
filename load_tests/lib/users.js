/**
 * Load-test user pool — shared k6 library.
 *
 * Reads LOAD_TEST_USERS_JSON from the Grafana Cloud environment variable
 * and assigns one of the 50 load-test users to each VU in a stable,
 * round-robin fashion.
 *
 * Usage:
 *   import { getUser } from '../lib/users.js';
 *   const user = getUser(__VU);   // {user_id, email, jwt}
 */

const raw = __ENV.LOAD_TEST_USERS_JSON;

if (!raw) {
  throw new Error(
    '[users.js] LOAD_TEST_USERS_JSON environment variable is not set.\n' +
    'Set it in Grafana Cloud: Performance → Default project → Settings → Environment variables.\n' +
    'Value should be the minified contents of /test_credentials/load_test_users.json.'
  );
}

let _pool;
try {
  const parsed = JSON.parse(raw);
  _pool = parsed.users;
} catch (e) {
  throw new Error(
    '[users.js] Failed to parse LOAD_TEST_USERS_JSON: ' + e.message + '\n' +
    'Ensure the value is valid JSON (minified contents of load_test_users.json).'
  );
}

if (!Array.isArray(_pool) || _pool.length === 0) {
  throw new Error('[users.js] LOAD_TEST_USERS_JSON parsed but contains no users.');
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
  const u = _pool[idx];
  return { user_id: u.user_id, email: u.email, jwt: u.jwt };
}

/** Total number of users in the pool (useful for assertions). */
export const poolSize = _pool.length;
