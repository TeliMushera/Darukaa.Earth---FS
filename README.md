# Darukaa.Earth

Full-stack geospatial dashboard for carbon and biodiversity projects.

## Stack
- Frontend: React + Vite + Mapbox GL JS + Mapbox Draw + Chart.js
- Backend: FastAPI + SQLAlchemy + JWT
- Database: PostgreSQL + PostGIS
- CI: GitHub Actions
- Code quality: ESLint + Prettier + Ruff + pre-commit

## Local setup

### 1. Database
The easiest local option is Docker:

```bash
docker compose up -d db
```

This starts PostgreSQL with PostGIS.

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Backend: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open the Vite URL shown in the terminal.

Set `VITE_MAPBOX_TOKEN` in `frontend/.env`.

## Demo flow

1. Register.
2. The backend creates a demo project automatically for the new user.
3. Open the project/site dashboard.
4. Click **Draw Site** and draw a polygon.
5. Enter a site name and save.
6. Click a site to see analytics.

## Environment variables

Backend:
- DATABASE_URL
- JWT_SECRET
- FRONTEND_URL

Frontend:
- VITE_API_URL
- VITE_MAPBOX_TOKEN

## CI/CD

GitHub Actions runs frontend build/lint and backend syntax/quality checks on pushes and pull requests.

Deployment can be done with:
- Frontend: Vercel
- Backend: Render
- PostgreSQL/PostGIS: Render PostgreSQL or another managed PostgreSQL provider with PostGIS enabled.

For production, set the same environment variables in the deployment platform.

## Schema

- users: authentication accounts
- projects: carbon/biodiversity projects
- sites: geographical sites with PostGIS Polygon geometry
- site_metrics: time-series environmental metrics

## Dataset choice

The analytics values are synthetic demonstration data. This is intentional because the challenge allows mock datasets and the MVP focuses on the geospatial application workflow rather than external environmental data collection.
