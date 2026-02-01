# QA Training Platform – Fly.io Deployment

## Prerequisites

- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- Fly.io account: `fly auth login`

## Deployment Order

Deploy in this order so URLs and CORS are correct:

1. **E-Commerce Lab** (optional, for return/refund mission)
2. **Backend API**
3. **Frontend**

## Quick Deploy

From project root:

```bash
cd backend
./deploy.sh
# Choose 4) Всё (лаба + backend + frontend)
```

Or deploy individually:

```bash
# Lab (ecommerce return/refund)
cd backend/labs/ecommerce_return_refund_lab && fly deploy

# Backend
cd backend && fly deploy

# Frontend (builds with backend URL baked in)
cd frontend && fly deploy
```

## Environment Variables

### Frontend (build-time, set in `frontend/fly.toml` or Docker build args)

| Variable         | Description                          | Production (Fly)                          |
|-----------------|--------------------------------------|-------------------------------------------|
| `VITE_API_URL`  | Backend API base URL                 | `https://qa-platform-backend.fly.dev`    |
| `VITE_DEMO_MODE`| `true` = mock data, `false` = API    | `false`                                   |

Local development: copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL=http://localhost:8080` and `VITE_DEMO_MODE=false` to use a local backend.

### Backend (runtime, set in `backend/fly.toml` or Fly secrets)

| Variable         | Description                    | Default (Fly)                              |
|-----------------|--------------------------------|--------------------------------------------|
| `FRONTEND_URL`  | Allowed CORS origin            | `https://qa-platform-frontend.fly.dev`    |
| `ECOM_LAB_URL`  | E-Commerce lab base URL        | `https://qa-lab-ecom-return-refund.fly.dev` |
| `PLATFORM_SECRET` | Secret for lab flag verification | `platform-secret-key` (change in prod)   |
| `DEBUG`         | Enable debug/reload            | `false`                                    |

## URLs After Deploy

| App    | URL |
|--------|-----|
| Frontend | https://qa-platform-frontend.fly.dev |
| Backend  | https://qa-platform-backend.fly.dev |
| Lab (E-Commerce) | https://qa-lab-ecom-return-refund.fly.dev |

## Health Checks

- **Frontend**: `GET /health` (nginx)
- **Backend**: `GET /health` (FastAPI)
- **Lab**: `GET /health` (lab app)

## Changing Backend URL for Frontend

Frontend uses `VITE_API_URL` at **build time**. To point to another backend:

1. **Fly.io**: set `[build.args]` in `frontend/fly.toml`:
   ```toml
   [build.args]
     VITE_API_URL = "https://your-backend.fly.dev"
     VITE_DEMO_MODE = "false"
   ```
2. **Local**: set in `frontend/.env` and run `npm run build`.
