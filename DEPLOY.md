# MedBand Railway Deployment



## Step 1: Install Railway CLI



```bash

npm install -g @railway/cli

```



## Step 2: Login to Railway



```bash

railway login

```



## Step 3: Create new project



```bash

railway init

```



## Step 4: Add shared state storage (required)

MedBand runs **5 separate Railway services** (web + 4 agents). Local `cases/*.json` files are **ephemeral and not shared** between services.

Choose one:

### Option A: PostgreSQL (recommended)

1. In Railway project: **Add service → Database → PostgreSQL**
2. Copy `DATABASE_URL` from the Postgres service
3. Add `DATABASE_URL` to **web**, **coordinator**, **intake**, **verification**, and **resource**

### Option B: Shared Railway volume

1. Create a volume mounted at `/data`
2. Attach the **same volume** to all 5 services
3. Set `MEDBAND_DATA_DIR=/data` on each service

Idempotency keys (`case_id + stage + sender + recipient`) and processed-message dedupe are stored in this shared backend.

## Step 5: Replicas (important)

Each agent service must run **exactly 1 replica**. If Coordinator or Intake has 2+ instances, both will process the same Band message and duplicate outputs.

In Railway: open each agent service → Settings → ensure **Replicas = 1**.

## Step 6: Add environment variables on Railway dashboard

Go to your Railway project > Variables tab.

Required for web service:

- `BAND_MODE=true`
- `AIML_API_KEY`
- `AIML_MODEL=gpt-4o-mini`
- `DATABASE_URL` (or `MEDBAND_DATA_DIR=/data`)
- `INTAKE_AGENT_ID` / `INTAKE_API_KEY`
- `COORDINATOR_AGENT_ID` / `COORDINATOR_API_KEY`

Add the same `DATABASE_URL` (or volume path) to all four agent services.

## Step 7: Deploy the web service (Flask form)



```bash

railway up -s web -d

```



## Step 8: Deploy 4 Band agent services



```bash

railway up -s coordinator -d

railway up -s intake -d

railway up -s verification -d

railway up -s resource -d

```



Or use `railway-start.py` with `SERVICE_TYPE` env var per service.



## Step 9: Get your public URL



Railway gives you a URL like: `web-production-6d13b.up.railway.app`

This is your live web form URL.



## Step 10: Human approval via Band



No separate dashboard deploy needed. Approvers log in at [app.band.ai](https://app.band.ai) and respond in MedBand case rooms.



See [demo_flow.md](../demo_flow.md) for the full demo script.

