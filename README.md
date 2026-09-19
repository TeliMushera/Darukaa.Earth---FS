# Darukaa.Earth

This is a full-stack geospatial platform for monitoring biodiversity, environmental conditions, and conservation sites.

It allows users to create environmental projects, add geographic monitoring sites by drawing polygons on an interactive map, and view environmental indicators and their changes over time.

---

## Overview

Darukaa.Earth connects:

- Interactive geographic mapping
- Project and site management
- PostgreSQL + PostGIS geospatial storage
- Environmental indicator tracking
- Time-series analytics
- JWT-based authentication

The platform is designed around the relationship between:

**Where → What → When**

- **Where:** Geographic monitoring site
- **What:** Environmental indicators
- **When:** Recorded observation over time

---

## Key Features

- User registration and login
- Create and manage environmental projects
- Add multiple monitoring sites
- Draw site boundaries directly on a Mapbox map
- Store site polygons using PostGIS
- View project and site information
- Track environmental indicators
- View historical data using charts
- PostgreSQL database with geospatial support
- REST API using FastAPI
- Responsive React dashboard

---

## How the System Works
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/615fc2d8-991f-45a4-ba78-3a39c3d2287a" />
---

## Environmental Data

The current hackathon implementation uses **synthetic/demo environmental data** for development and demonstration.

The backend generates six observations for every newly created site.

| Metric | Current Generation |
|---|---|
| Carbon | `55 + i × 5 + random(-2, 2)` |
| Biodiversity | `60 + i × 4 + random(-2, 2)` |
| Soil Health | `62 + i × 3 + random(-2, 2)` |
| Water Availability | `65 + i × 2 + random(-2, 2)` |
| Habitat Quality | `58 + i × 5 + random(-2, 2)` |

The observations are stored with dates approximately one month apart and displayed as time-series charts.

**Important:** The current version does not use live satellite data, sensors, NASA data, or external environmental APIs. Chart.js only visualizes the values returned by the backend; it does not generate the environmental values.

---

## Map & Geospatial Data

Mapbox provides the interactive map and drawing interface.

When a user draws a monitoring site:

```text
Mapbox Drawing
      ↓
GeoJSON Polygon
      ↓
FastAPI
      ↓
PostGIS
      ↓
Stored Site Geometry
      ↓
Mapbox Visualization
```

Site geometry is stored as:

```
POLYGON — SRID 4326
```

The map itself comes from Mapbox, while the project/site polygons are created and stored by the application.

---

## Dashboard Data

The dashboard combines database information and application calculations.

- **Sites:** Number of sites stored in the database.
- **Tracked Area:** Currently uses the site's stored area value. The initial demo site has a predefined value; automatic polygon-area calculation is not yet implemented.
- **Eco Score:** Prototype dashboard indicator used for demonstration and is not a scientifically validated environmental score.

---

## Database

The application uses Supabase PostgreSQL with PostGIS.

### Main Tables

```text
users
 └── projects
      └── sites
           └── site_metrics
```

**users**
```
id
name
email
password_hash
```

**projects**
```
id
name
description
project_type
created_by
created_at
```

**sites**
```
id
project_id
name
status
area
location
created_at
```

**site_metrics**
```
id
site_id
date
carbon_value
biodiversity_score
soil_health
water_availability
habitat_quality
```

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login |
| GET | `/projects` | Get user's projects |
| POST | `/projects` | Create project |
| GET | `/projects/{id}/sites` | Get project sites |
| POST | `/projects/{id}/sites` | Create site |
| GET | `/sites/{id}` | Get site details |
| GET | `/sites/{id}/analytics` | Get site metrics |
| GET | `/health` | API health check |

---

## Technology Stack

**Frontend**
- React
- Vite
- Mapbox GL JS
- Mapbox GL Draw
- Chart.js

**Backend**
- Python
- FastAPI
- SQLAlchemy
- GeoAlchemy2
- JWT Authentication

**Database**
- PostgreSQL
- PostGIS
- Supabase

**Development**
- Git & GitHub
- GitHub Actions
- Ruff
- Pre-commit

---

## Project Structure

```
Darukaa.Earth/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env
│
├── .github/
│   └── workflows/
│
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## Local Setup

### Requirements

Install:

- Git
- Python 3.11+
- Node.js 18+
- npm
- Supabase account
- Mapbox account

### 1. Clone Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Darukaa.Earth
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=your_supabase_postgresql_connection_string
JWT_SECRET=your_long_random_secret
FRONTEND_URL=http://localhost:5173
```

Start backend:

```bash
uvicorn main:app --reload
```

Backend: `http://127.0.0.1:8000`

Health check: `http://127.0.0.1:8000/health`

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_MAPBOX_TOKEN=your_mapbox_access_token
```

Start frontend:

```bash
npm run dev
```

Open: `http://localhost:5173`

### 4. First Use

1. Register an account.
2. Login.
3. Create/open a project.
4. Draw a monitoring site on the map.
5. Create the site — geometry is stored in PostGIS.
6. Demo environmental metrics are generated.
7. Open the site analytics to view the graphs.

---

## CI/CD & Code Quality

GitHub Actions is used for automated checks. The project also includes:

- Ruff linting
- Pre-commit configuration
- Environment variable protection
- Separate frontend/backend configuration

Secrets such as database credentials, JWT secrets, and Mapbox tokens are stored in environment variables and are not committed to GitHub.

---

## Current Implementation

The current version focuses on the core geospatial monitoring workflow:

```
Authentication → Projects → Sites → Map → PostGIS → Environmental Metrics → Analytics
```

The environmental metrics are currently synthetic data for demonstration. The architecture can later be connected to real environmental datasets and additional geospatial analysis services.

---

## Summary

Darukaa.Earth provides a full-stack foundation for managing environmental projects and geographic monitoring sites.

The system combines:

```
React + Mapbox → FastAPI → PostgreSQL/PostGIS → Analytics
```

with secure authentication, geospatial site storage, environmental indicators, and time-series visualization.
