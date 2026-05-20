/**
 * Reusable request groups — shared k6 library.
 *
 * Each function represents one realistic user behaviour pattern.
 * All requests are tagged for threshold isolation.
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';

const TARGET = __ENV.TARGET_URL;

if (!TARGET) {
  throw new Error(
    '[scenarios.js] TARGET_URL environment variable is not set.\n' +
    'Set it in Grafana Cloud environment variables: the full Railway production URL\n' +
    '(e.g. https://your-service.up.railway.app).'
  );
}

/** Shared headers builder */
function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

/** Random sleep between min and max seconds (simulates think time) */
function thinkTime(min, max) {
  sleep(min + Math.random() * (max - min));
}

/**
 * Simulates a user browsing their dashboard.
 * Non-AI, DB-only endpoints. Core throughput path.
 * Tag: browse
 */
export function browseDashboard(token) {
  const headers = authHeaders(token);
  const params = { tags: { endpoint: 'browse' } };

  group('browse_dashboard', () => {
    const health = http.get(`${TARGET}/api/health`, { tags: { endpoint: 'browse' } });
    check(health, { 'health 200': (r) => r.status === 200 });
    thinkTime(0.5, 1.5);

    const me = http.get(`${TARGET}/api/auth/me`, { headers, ...params });
    check(me, { 'me 200': (r) => r.status === 200 });
    thinkTime(0.5, 1.5);

    const stats = http.get(`${TARGET}/api/progress/stats`, { headers, ...params });
    check(stats, { 'stats 200': (r) => r.status === 200 });
    thinkTime(1, 2);

    const convos = http.get(`${TARGET}/api/progress/conversations`, { headers, ...params });
    check(convos, { 'conversations 200': (r) => r.status === 200 });
    thinkTime(1, 3);
  });
}

/**
 * Simulates a user browsing their flashcard sets.
 * DB-only. Tests flashcard index performance.
 * Tag: flashcards
 */
export function browseFlashcards(token) {
  const headers = authHeaders(token);
  const params = { tags: { endpoint: 'flashcards' } };

  group('browse_flashcards', () => {
    const sets = http.get(`${TARGET}/api/flashcards/sets`, { headers, ...params });
    check(sets, { 'flashcard sets 200': (r) => r.status === 200 });
    thinkTime(1, 2);

    const due = http.get(`${TARGET}/api/flashcards/due`, { headers, ...params });
    check(due, { 'flashcards due 200': (r) => r.status === 200 });
    thinkTime(1, 2);
  });
}

/**
 * Simulates a user requesting conversation help mid-session.
 * Triggers a real gpt-4o-mini call. Rate-capped at the scenario level.
 * Estimated cost: ~$0.001 per call.
 * Tag: ai_help
 */
export function triggerAIHelp(token) {
  const headers = Object.assign(authHeaders(token), { 'Content-Type': 'application/json' });

  const payload = JSON.stringify({
    ai_response: "Muy bien! ¿Cómo puedo ayudarte hoy?",
    conversation_context: [
      { role: "user", content: "Hola, quiero practicar español." },
      { role: "assistant", content: "Muy bien! ¿Cómo puedo ayudarte hoy?" }
    ],
    target_language: "spanish",
    user_language: "english",
    proficiency_level: "B1",
    session_id: `load-test-${__VU}-${Date.now()}`,
    request_type: "hint"
  });

  const res = http.post(`${TARGET}/api/conversation-help/generate`, payload, {
    headers,
    tags: { endpoint: 'ai_help' },
    timeout: '10s',
  });

  check(res, {
    'ai_help 2xx': (r) => r.status >= 200 && r.status < 300,
    'ai_help not 500': (r) => r.status !== 500,
  });
}

/**
 * Simulates a user starting a voice session (token mint only — no audio).
 * Hits OpenAI Sessions API for an ephemeral key. Rate-capped at scenario level.
 * Estimated cost: ~$0.0005 per call (session creation without audio).
 * Tag: realtime_token
 */
export function startVoiceSession(token) {
  const headers = Object.assign(authHeaders(token), { 'Content-Type': 'application/json' });

  const payload = JSON.stringify({
    language: "dutch",
    level: "B1",
    selected_duration: 3,
  });

  const res = http.post(`${TARGET}/api/realtime/token`, payload, {
    headers,
    tags: { endpoint: 'realtime_token' },
    timeout: '15s',
  });

  check(res, {
    'realtime_token 2xx': (r) => r.status >= 200 && r.status < 300,
    'realtime_token not 500': (r) => r.status !== 500,
  });
}
