# How to Deploy AgentShield

AgentShield is a FastAPI trust layer plus a Vite React dashboard. This guide covers local run, a public host, and the optional x402 / Algorand payment pieces.

## What you are deploying

| Piece | Path | Role |
|---|---|---|
| Trust API | `backend/main.py` | FastAPI app on port `8000` |
| Dashboard | `frontend/` | Vite React app (`npm run dev` or `frontend/dist`) |
| Audit DB | `agentshield.db` | SQLite file created on first API start |
| AI agent (optional) | `ai/agent.py` | Calls the API to analyze and authorize |
| x402 provider (optional) | `backend/paid_provider.py` | Paid weather endpoint |
| x402 client (optional) | `backend/client.py` | Algorand x402 settle via GoPlausible |
| Algorand test payment (optional) | `backend/algorand.py` | Testnet ALGO transfer |

The dashboard talks to the API over HTTP. Set `VITE_API_URL` in `frontend/.env` to the address browsers will use. The UI never hardcodes an API host, network, or PayTo address.

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- Git
- A host that can bind port `8000` (local machine, VPS, or a PaaS)
- For x402 payments: an Algorand buyer wallet opted into USDC on the selected network

## 1. Clone and install

```bash
git clone https://github.com/<your-org>/AgentShield-FusioniX.git
cd AgentShield-FusioniX

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

python -m pip install -r requirements.txt
```

Always start the API with `python -m uvicorn`, not the bare `uvicorn` command. On macOS, Homebrew's `uvicorn` sits on `PATH` ahead of the venv and uses its own Python, which does not have FastAPI. That produces `ModuleNotFoundError: No module named 'fastapi'` even when the venv is active.

`requirements.txt` already includes `x402-avm` and `py-algorand-sdk`.

Always start the API from the **repository root** so Python can resolve the `backend` package:

```bash
cd /path/to/AgentShield-FusioniX
```

## 2. Environment variables

Only three names are required.

### Backend (repo-root `.env`)

```bash
cp .env.example .env
```

```bash
ALGORAND_NETWORK=testnet
PAY_TO=
```

`PAY_TO` is the Algorand receiver address. The API will not start without it. Never hardcode it in the UI.

Set `ALGORAND_NETWORK=mainnet` only when you intend live funds.

Facilitator, Testnet paid weather URL, and algod hosts stay as code defaults. `GET /payment/status` returns `pay_to` and `network_id` from env.

### Frontend (`frontend/.env`)

```bash
cp frontend/.env.example frontend/.env
```

```bash
VITE_API_URL=http://127.0.0.1:8000
```

LAN or public host: `VITE_API_URL=http://YOUR_HOST_OR_IP:8000`

HTTPS production: `VITE_API_URL=https://api.example.com`

If you skip this step, the UI will look online but every request will fail.

**Analyze Trust** asks Pera (QR or extension) to sign x402, the [GoPlausible facilitator](https://facilitator.goplausible.xyz/) settles on Algorand, then the trust score is shown. If settlement fails, no score is shown.

The connected wallet must:

1. Hold a little ALGO (opt-in min-balance)
2. Opt in to USDC (`10458941` on Testnet, `31566704` on Mainnet)
3. Hold at least `0.001` USDC (`1000` atomic units)

Circle's Testnet USDC faucet: https://faucet.circle.com/

Never commit `.env` files. They are already listed in `.gitignore`.

## 3. Run locally

### Backend

From the repository root:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Check:

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Providers: [http://127.0.0.1:8000/providers](http://127.0.0.1:8000/providers)
- Payment status: [http://127.0.0.1:8000/payment/status](http://127.0.0.1:8000/payment/status)

SQLite creates `agentshield.db` in the working directory on first start. That file is the audit ledger. Keep it if you want transaction history to survive restarts.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

The dashboard should show **SYSTEM ONLINE**, load three demo providers, and let you **Analyze Trust** / **Use Service**.

### Optional: AI agent

```bash
export AGENTSHIELD_API=http://127.0.0.1:8000
python -m ai.agent
```

### Optional: x402 paid provider + client

Terminal A — paid resource (different port from the trust API):

```bash
python -m uvicorn backend.paid_provider:app --host 0.0.0.0 --port 8001
```

Terminal B — settle the same Algorand x402 payment Analyze uses:

```bash
python -m backend.client
```

### Optional: Algorand Testnet payment

```bash
python backend/algorand_payment_test.py
```

Fund the printed buyer address from an Algorand Testnet dispenser, then run the script again.

## 4. Production frontend build

```bash
cd frontend
cp .env.example .env
# set VITE_API_URL to the public API URL
npm install
npm run build
```

Serve `frontend/dist` as a static site.

### Vercel (dashboard only)

Vercel hosts the Vite React dashboard. The FastAPI backend is not a Vercel Python app — deploy it on a VPS or a Python PaaS (section 6) and point the UI at it.

In the Vercel project settings:

1. **Root Directory** = `frontend` (not `backend`, not `.`).
2. **Framework Preset** = Vite.
3. Clear any custom **Install Command** / **Build Command** overrides. `frontend/vercel.json` runs `npm run build` and outputs `dist`.
4. Set the build env var `VITE_API_URL` to the public API URL (for example `https://api.example.com`).

If Root Directory is left as `backend`, `npm install --prefix frontend` looks for `backend/frontend/package.json` and fails with `ENOENT`.

`requirements.txt` must be UTF-8. A UTF-16 copy makes Vercel fail with `Failed to parse "requirements.txt"` and garbled content such as `��c`.

## 5. Deploy on a VPS

Use this when you have a Linux box with a public IP or domain.

1. Install Python and Node, create a venv, and install the packages from section 1.
2. Copy the repo onto the server (git clone or `rsync`).
3. Set repo-root `.env` with `ALGORAND_NETWORK` and `PAY_TO`.
4. Build the dashboard with `VITE_API_URL` set to `http://YOUR_PUBLIC_IP:8000` or your HTTPS API URL.
5. Start the API with a process manager so it survives logout:

```bash
pip install gunicorn
gunicorn backend.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Use **one worker**. SQLite does not handle concurrent writers well.

Example `systemd` unit (`/etc/systemd/system/agentshield.service`):

```ini
[Unit]
Description=AgentShield API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/AgentShield-FusioniX
Environment="PATH=/opt/AgentShield-FusioniX/.venv/bin"
ExecStart=/opt/AgentShield-FusioniX/.venv/bin/gunicorn backend.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

6. Serve the built dashboard and reverse-proxy the API with nginx:

```nginx
server {
    listen 80;
    server_name example.com;

    root /opt/AgentShield-FusioniX/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

If you use the `/api/` prefix, build the frontend with:

```bash
VITE_API_URL=https://example.com/api
```

Add TLS with Certbot (`sudo certbot --nginx`). After HTTPS is on, browsers will block mixed-content calls to `http://`.

Open the firewall for `80` / `443`. Do not expose SQLite or `.env`.

## 6. Deploy on a PaaS (Render, Railway, Fly)

The API is a standard ASGI app. The start command is:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

If the platform does not inject `PORT`, use `8000`.

Notes for these hosts:

- Set the root directory to the repo root.
- Persist `agentshield.db` on a volume, or transaction history resets on every deploy.
- Host `frontend/dist` as a static site (same platform or GitHub Pages / Cloudflare Pages / Netlify).
- After you know the public API URL, set `VITE_API_URL` and rebuild the dashboard.
- CORS on the API is currently `allow_origins=["*"]`, so a split frontend/API origin will work. Tighten this before a real production launch.

## 7. Confirm the deploy

```bash
curl -s http://YOUR_HOST:8000/health
# {"status":"healthy"}

curl -s http://YOUR_HOST:8000/providers
# three demo providers

curl -s http://YOUR_HOST:8000/payment/status
# includes pay_to and network_id from env
```

In the dashboard:

1. Status dot is online.
2. Three provider cards appear.
3. **Analyze Trust** settles x402, then opens the modal with a score and `APPROVE` / `REVIEW` / `BLOCK`.
4. **Use Service** writes a row that shows up under Transaction History.

| Expected demo | Trust | Decision |
|---|---|---|
| Weather Intelligence API | high | `APPROVE` |
| FastWeather API | medium | `REVIEW` |
| UnknownWeather API | low | `BLOCK` |

## 8. Production checklist

- [ ] `VITE_API_URL` matches the live API, including `https://` if TLS is enabled
- [ ] `ALGORAND_NETWORK` and `PAY_TO` are set on the API
- [ ] `.env` files are on the server only, never in git
- [ ] SQLite file is on persistent disk, or you accept an empty ledger after restart
- [ ] Process manager or PaaS keeps `uvicorn` / `gunicorn` running
- [ ] CORS origins are restricted to your dashboard origin
- [ ] x402 / Algorand keys are testnet-only unless you intend live settlement
- [ ] `/health` is the uptime probe

## Decision model (unchanged in deploy)

| Trust score | Risk | Decision |
|---|---|---|
| 80–100 | LOW | `APPROVE` |
| 60–79 | MEDIUM | `REVIEW` |
| Below 60 | HIGH | `BLOCK` |

Authorization also rejects large amounts: even a trusted provider goes to `REVIEW` when `amount > 10`.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Homebrew `uvicorn` ran instead of the venv | `python -m pip install -r requirements.txt` then `python -m uvicorn ...` |
| API exits with `PAY_TO is required` | Missing receiver address | Set `PAY_TO` in the repo-root `.env` |
| API exits with `ALGORAND_NETWORK must be...` | Missing or invalid network | Set `ALGORAND_NETWORK=testnet` or `mainnet` |
| Dashboard says backend unavailable | Wrong `VITE_API_URL` or API not running | Section 2 and `/health` |
| Browser blocks the request | HTTPS page calling HTTP API, or CORS | Use TLS on both, or keep both on HTTP for a lab |
| Empty transaction history after restart | Ephemeral disk | Persist `agentshield.db` |
| Analyze shows no score | x402 settlement failed (wallet, USDC opt-in, or balance) | Section 2 and `/payment/status` |
| Algorand script exits after printing an address | Buyer has no Testnet ALGO | Fund it, then rerun |
