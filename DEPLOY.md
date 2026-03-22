# Deploying Churn Insight to Railway

## Prerequisites

- A [Railway](https://railway.app) account
- This repo pushed to GitHub
- API keys for Anthropic, OpenAI, and Resend

---

## Steps

### 1. Create a new Railway project

Go to [railway.app/new](https://railway.app/new) → **Deploy from GitHub repo** → select this repo.

### 2. Add a Postgres database

Inside the project, click **+ New** → **Database** → **PostgreSQL**.
Railway provisions the database and sets `DATABASE_URL` automatically in the internal network.

### 3. Link DATABASE_URL to the web service

In the web service's **Variables** tab, add:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

This uses Railway's [reference variable](https://docs.railway.app/develop/variables#reference-variables) syntax to pull the Postgres URL into your service.

### 4. Set all environment variables

In the web service **Variables** tab, add each variable below:

| Variable | Where to get it |
|---|---|
| `DATABASE_URL` | Set via reference variable (step 3) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com/keys](https://console.anthropic.com/keys) |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `TYPEFORM_CLIENT_ID` | Typeform → Settings → Connected apps |
| `TYPEFORM_CLIENT_SECRET` | Same as above |
| `TYPEFORM_REDIRECT_URI` | `https://<your-railway-domain>/api/v1/integrations/typeform/callback` |
| `DELIGHTED_API_KEY` | Delighted → Settings → API |
| `JWT_SECRET_KEY` | Run: `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | Run: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `STRIPE_SECRET_KEY` | [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys) |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Webhooks → your endpoint → Signing secret |
| `RESEND_API_KEY` | [resend.com/api-keys](https://resend.com/api-keys) |
| `FRONTEND_URL` | Your Lovable app URL, e.g. `https://yourapp.lovable.app` |
| `ADMIN_SECRET` | Run: `python -c "import secrets; print(secrets.token_hex(16))"` |

### 5. Deploy

Railway auto-deploys on every push to `main`. The `CMD` in the Dockerfile runs:

```
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Migrations run automatically before the server starts.

---

## Post-deploy verification

### Health check

```bash
curl https://<your-railway-domain>/
# → {"status": "ok", "version": "0.1.0"}
```

### Register your account

```bash
curl -X POST https://<your-railway-domain>/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```

### Activate your plan (no billing yet)

```bash
curl -X PUT https://<your-railway-domain>/api/v1/admin/account/plan \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: <your-ADMIN_SECRET>" \
  -d '{"account_id": "<your-account-id>", "plan": "solo"}'
```

---

## Notes

### Ephemeral filesystem

Railway's filesystem is ephemeral — `data/embeddings/` is lost on redeploy.
For production, move embedding storage to S3 or Cloudflare R2 by updating
`save_embeddings` / `load_embeddings` in `app/services/embeddings.py`.

### Scaling

The default Railway plan runs a single container. The APScheduler weekly job
runs inside the same process. If you scale to multiple replicas, only one
instance should run the scheduler — add a `SCHEDULER_ENABLED=true` env var
and guard `start_scheduler()` behind it.

### Logs

```bash
railway logs
```
