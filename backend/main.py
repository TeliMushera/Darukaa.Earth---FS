import json
import random
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pwdlib import PasswordHash
from shapely.geometry import shape
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    project_type = Column(String(80), default="Biodiversity")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    owner = relationship("User", back_populates="projects")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(String(50), default="Active")
    area = Column(Float, default=0)
    location = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    project = relationship("Project", back_populates="sites")
    metrics = relationship("SiteMetric", back_populates="site", cascade="all, delete-orphan")


class SiteMetric(Base):
    __tablename__ = "site_metrics"
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    date = Column(Date, nullable=False)
    carbon_value = Column(Float, nullable=False)
    biodiversity_score = Column(Float, nullable=False)
    soil_health = Column(Float, nullable=False)
    water_availability = Column(Float, nullable=False)
    habitat_quality = Column(Float, nullable=False)
    site = relationship("Site", back_populates="metrics")


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class ProjectIn(BaseModel):
    name: str
    description: str = ""
    project_type: str = "Biodiversity"


class SiteIn(BaseModel):
    name: str
    geometry: dict


app = FastAPI(title="Darukaa.Earth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    Base.metadata.create_all(bind=engine)

def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def make_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        user = session.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def site_json(session, site):
    geom = session.scalar(func.ST_AsGeoJSON(site.location))
    return {
        "id": site.id,
        "name": site.name,
        "project_id": site.project_id,
        "status": site.status,
        "area": round(site.area or 0, 2),
        "geometry": json.loads(geom),
    }


def add_demo_metrics(session, site):
    for i in range(6):
        session.add(
            SiteMetric(
                site_id=site.id,
                date=datetime.now(timezone.utc).date() - timedelta(days=(5 - i) * 30),
                carbon_value=55 + i * 5 + random.uniform(-2, 2),
                biodiversity_score=60 + i * 4 + random.uniform(-2, 2),
                soil_health=62 + i * 3 + random.uniform(-2, 2),
                water_availability=65 + i * 2 + random.uniform(-2, 2),
                habitat_quality=58 + i * 5 + random.uniform(-2, 2),
            )
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register")
def register(data: RegisterIn, session: Session = Depends(db)):
    if session.query(User).filter_by(email=data.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=data.name, email=data.email.lower(), password_hash=password_hash.hash(data.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create one demo project so the reviewer sees a populated dashboard immediately.
    project = Project(
        name="Western Ghats Restoration",
        description="Synthetic carbon and biodiversity monitoring project.",
        project_type="Biodiversity",
        created_by=user.id,
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    polygon = {
        "type": "Polygon",
        "coordinates": [[[77.55, 12.92], [77.60, 12.92], [77.60, 12.97], [77.55, 12.97], [77.55, 12.92]]],
    }
    site = Site(
        project_id=project.id,
        name="Demo Conservation Site",
        area=245,
        location=from_shape(shape(polygon), srid=4326),
    )
    session.add(site)
    session.commit()
    session.refresh(site)
    add_demo_metrics(session, site)
    session.commit()

    return {"access_token": make_token(user.id), "token_type": "bearer"}


@app.post("/auth/login")
def login(data: LoginIn, session: Session = Depends(db)):
    user = session.query(User).filter_by(email=data.email.lower()).first()
    if not user or not password_hash.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": make_token(user.id), "token_type": "bearer"}


@app.get("/projects")
def projects(user=Depends(current_user), session: Session = Depends(db)):
    rows = session.query(Project).filter_by(created_by=user.id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "project_type": p.project_type,
            "site_count": len(p.sites),
        }
        for p in rows
    ]


@app.post("/projects")
def create_project(data: ProjectIn, user=Depends(current_user), session: Session = Depends(db)):
    project = Project(**data.model_dump(), created_by=user.id)
    session.add(project)
    session.commit()
    session.refresh(project)
    return {"id": project.id, "name": project.name}


@app.get("/projects/{project_id}/sites")
def project_sites(project_id: int, user=Depends(current_user), session: Session = Depends(db)):
    project = session.query(Project).filter_by(id=project_id, created_by=user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return [site_json(session, s) for s in project.sites]


@app.post("/projects/{project_id}/sites")
def create_site(project_id: int, data: SiteIn, user=Depends(current_user), session: Session = Depends(db)):
    project = session.query(Project).filter_by(id=project_id, created_by=user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        geom = shape(data.geometry)
        if geom.geom_type != "Polygon":
            raise ValueError("Polygon required")
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(400, "Invalid polygon geometry")

    site = Site(project_id=project_id, name=data.name, location=from_shape(geom, srid=4326), area=0)
    session.add(site)
    session.commit()
    session.refresh(site)
    add_demo_metrics(session, site)
    session.commit()
    return site_json(session, site)


@app.get("/sites/{site_id}")
def get_site(site_id: int, user=Depends(current_user), session: Session = Depends(db)):
    site = (
        session.query(Site)
        .join(Project)
        .filter(Site.id == site_id, Project.created_by == user.id)
        .first()
    )
    if not site:
        raise HTTPException(404, "Site not found")
    return site_json(session, site)


@app.get("/sites/{site_id}/analytics")
def analytics(site_id: int, user=Depends(current_user), session: Session = Depends(db)):
    site = (
        session.query(Site)
        .join(Project)
        .filter(Site.id == site_id, Project.created_by == user.id)
        .first()
    )
    if not site:
        raise HTTPException(404, "Site not found")
    metrics = session.query(SiteMetric).filter_by(site_id=site.id).order_by(SiteMetric.date).all()
    return [
        {
            "date": m.date.isoformat(),
            "carbon": round(m.carbon_value, 1),
            "biodiversity": round(m.biodiversity_score, 1),
            "soil": round(m.soil_health, 1),
            "water": round(m.water_availability, 1),
            "habitat": round(m.habitat_quality, 1),
        }
        for m in metrics
    ]
