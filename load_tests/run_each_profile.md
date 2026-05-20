# Running the Load Test Profiles

Run these commands in order. Each profile must pass its GO/NO-GO
criteria before proceeding to the next.

**Prerequisites:**
- [ ] `create_load_test_users.py` has been run (50 users in MongoDB)
- [ ] `LOAD_TEST_USERS_JSON` env var set in Grafana Cloud (see `setup/upload_jwts_to_grafana.md`)
- [ ] `TARGET_URL` env var set in Grafana Cloud (your Railway production URL)
- [ ] k6 CLI authenticated: `k6 cloud login --token <your-grafana-token>`

---

## Profile 01 — Smoke (~2 min, $0)

```bash
k6 cloud load_tests/profiles/01_smoke.js
```

**During:** Watch for any non-200 responses in the Grafana Cloud run output.

**GO criteria:**
- All thresholds green (p95 < 300ms, error rate < 0.1%)
- No unexpected 4xx/5xx in logs

**NO-GO:** Any threshold breach or unexpected errors → investigate before proceeding.

---

## Profile 02 — Load Nominal (~22 min, ~$2)

```bash
k6 cloud load_tests/profiles/02_load_nominal.js
```

**During:** Watch Railway Metrics tab for CPU and memory.

**GO criteria:**
- All thresholds green
- Railway CPU stays below 80%, memory plateaus
- MongoDB connections stay below 400

**NO-GO:** Any threshold breach → record the failing endpoint and VU count.

---

## Profile 03 — Stress Ramp (~35 min, ~$8)

```bash
k6 cloud load_tests/profiles/03_stress_ramp.js
```

**Expected behaviour:** Thresholds WILL breach at some VU step — that's the point.
Record which VU level first caused each threshold to fail.

**After run:**
- Note: "Browse p95 breached 500ms at X VUs"
- Note: "Error rate exceeded 1% at Y VUs"
- These are your Q1 and Q2 answers.

**Cleanup intermediate test data (optional if accumulated data is large):**
```bash
python load_tests/setup/cleanup_load_test_data.py --dry-run
# If counts look excessive, run without --dry-run
```

**GO criteria:** System recovered (Railway metrics returned to baseline) → proceed.

---

## Profile 04 — Spike (~11 min, ~$3)

```bash
k6 cloud load_tests/profiles/04_spike.js
```

**After run:** In Grafana Cloud timeseries chart:
1. Find p95 for `browse` endpoint in minutes 1–3 (pre-spike baseline).
2. Find p95 for `browse` endpoint in minutes 8–11 (post-spike recovery).
3. Recovery is clean if final p95 ≤ 2× pre-spike p95.

**GO criteria:**
- System survived (no 5xx spike)
- Recovery confirmed within 60s of dropping VUs
- Overall error rate < 5%

---

## Profile 05 — Soak (65 min, ~$5)

```bash
k6 cloud load_tests/profiles/05_soak.js
```

**During the run:**
- Railway Metrics → Memory: watch for continuous upward trend (leak)
- Railway Metrics → CPU: should plateau, not climb

**After run:** Compare p95 in Grafana Cloud:
- Minutes 2–7 (early): record p95
- Minutes 58–63 (late): record p95
- Degradation threshold: late p95 must be ≤ 120% of early p95

**GO criteria:**
- All thresholds green
- Memory plateaued (no leak)
- p95 degradation ≤ 20%

---

## Final Cleanup

```bash
python load_tests/setup/cleanup_load_test_data.py
# Type 'DELETE LOAD TEST DATA' when prompted
```

---

## Estimated Total
| Profile | Duration | OpenAI cost |
|---|---|---|
| 01 Smoke | ~2 min | $0 |
| 02 Load Nominal | ~22 min | ~$2 |
| 03 Stress Ramp | ~35 min | ~$8 |
| 04 Spike | ~11 min | ~$3 |
| 05 Soak | ~65 min | ~$5 |
| **Total** | **~135 min** | **~$18** |
