# Uploading Load-Test JWTs to Grafana Cloud k6

After running `create_load_test_users.py`, you have 50 user JWTs in
`/test_credentials/load_test_users.json`. The k6 cloud runner needs
these to authenticate requests. Choose Option A (recommended).

---

## Option A — Single env var (recommended)

**Why:** One copy-paste action, no API calls, works with any k6 cloud project.

**Steps:**

1. Minify the credentials file:
   ```bash
   python3 -c "
   import json, sys
   with open('test_credentials/load_test_users.json') as f:
       d = json.load(f)
   print(json.dumps(d, separators=(',', ':')))
   " | pbcopy
   # (pbcopy puts it in your clipboard on macOS)
   ```

2. In Grafana Cloud:
   - Go to **Performance → Default project → Settings → Environment variables**
   - Click **Add variable**
   - Name: `LOAD_TEST_USERS_JSON`
   - Value: paste the minified JSON from your clipboard
   - Click **Save**

3. Also add:
   - Name: `TARGET_URL`
   - Value: your Railway production URL (e.g. `https://your-app.up.railway.app`)
   - Click **Save**

4. Verify in the k6 UI that both variables appear with non-empty values.

---

## Option B — Individual env vars via API (cleaner, more setup)

**Why:** Each VU can read its own JWT without parsing the full JSON.
**Tradeoff:** 52 API calls to set up.

**Grafana k6 API reference:**
- Base URL: `https://api.k6.io/v3`
- Auth: Bearer token from Grafana Cloud → Account → API Keys → Create token
- Project ID: `7601757`

**Script to upload all 50 JWTs:**
```bash
#!/bin/bash
# Requires: jq, your Grafana API token in $GRAFANA_TOKEN
API_TOKEN="<your-grafana-api-token>"
PROJECT_ID="7601757"

# Upload TARGET_URL
curl -s -X POST "https://api.k6.io/v3/projects/${PROJECT_ID}/environment-variables" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"TARGET_URL","value":"https://your-app.up.railway.app"}'

# Upload each JWT
jq -r '.users[] | "\(.index) \(.jwt)"' test_credentials/load_test_users.json | \
while read idx jwt; do
  padded=$(printf "%02d" $idx)
  curl -s -X POST "https://api.k6.io/v3/projects/${PROJECT_ID}/environment-variables" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"USER_${padded}_JWT\",\"value\":\"${jwt}\"}"
  echo "Uploaded USER_${padded}_JWT"
done
```

If using Option B, update `lib/users.js` to read `__ENV[`USER_${id}_JWT`]`
instead of parsing `LOAD_TEST_USERS_JSON`.

---

## Default recommendation: **Option A**

Option A is simpler, requires no API token, and the `lib/users.js` parser
handles it correctly. Only choose Option B if you need per-VU isolation
at the environment-variable level.
