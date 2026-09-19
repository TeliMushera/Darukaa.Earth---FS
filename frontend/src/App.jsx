import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { Chart, registerables } from "chart.js";
import { Line } from "react-chartjs-2";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";
import "mapbox-gl/dist/mapbox-gl.css";
import "./styles.css";

Chart.register(...registerables);

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

async function request(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function Auth({ onLogin }) {
  const [register, setRegister] = useState(true);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await request(register ? "/auth/register" : "/auth/login", {
        method: "POST",
        body: JSON.stringify(form),
      });
      localStorage.setItem("token", data.access_token);
      onLogin();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="auth">
      <div className="auth-card">
        <div className="brand">
          Darukaa<span>.Earth</span>
        </div>
        <p className="muted">Carbon & biodiversity intelligence</p>
        <h2>{register ? "Create account" : "Welcome back"}</h2>
        <form onSubmit={submit}>
          {register && (
            <input
              placeholder="Full name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          )}
          <input
            type="email"
            placeholder="Email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <input
            type="password"
            placeholder="Password"
            required
            minLength="6"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          {error && <div className="error">{error}</div>}
          <button>{register ? "Create account" : "Login"}</button>
        </form>
        <button className="link" onClick={() => setRegister(!register)}>
          {register ? "Already have an account? Login" : "Create a new account"}
        </button>
      </div>
    </div>
  );
}

function MapPanel({ projectId, sites, onSaved, onSelect }) {
  const ref = useRef();
  const map = useRef();
  const draw = useRef();
  const [drawing, setDrawing] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    if (!ref.current || map.current) return;
    map.current = new mapboxgl.Map({
      container: ref.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [77.59, 12.95],
      zoom: 11,
    });
    draw.current = new MapboxDraw({
      displayControlsDefault: false,
      controls: { polygon: true, trash: true },
    });
    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
    map.current.addControl(draw.current, "top-right");
    map.current.on("draw.create", () => {
      setDrawing(true);
    });
    return () => map.current?.remove();
  }, []);

  useEffect(() => {
    if (!map.current) return;

    for (const s of sites) {
      const id = `site-${s.id}`;
      const lineId = `${id}-line`;

      // Remove layers first
      if (map.current.getLayer(lineId)) {
        map.current.removeLayer(lineId);
      }

      if (map.current.getLayer(id)) {
        map.current.removeLayer(id);
      }

      // Then remove the source
      if (map.current.getSource(id)) {
        map.current.removeSource(id);
      }

      // Add source
      map.current.addSource(id, {
        type: "geojson",
        data: {
          type: "Feature",
          geometry: s.geometry,
          properties: { id: s.id },
        },
      });

      // Add polygon layer
      map.current.addLayer({
        id,
        type: "fill",
        source: id,
        paint: {
          "fill-color": "#1f6f5b",
          "fill-opacity": 0.35,
        },
      });

      // Add outline layer
      map.current.addLayer({
        id: lineId,
        type: "line",
        source: id,
        paint: {
          "line-color": "#14513f",
          "line-width": 2,
        },
      });

      map.current.on("click", id, () => onSelect(s));
    }
  }, [sites, onSelect]);

  async function save() {
    const all = draw.current.getAll();
    if (!all.features.length || !name.trim())
      return alert("Draw a polygon and enter a site name.");
    await request(`/projects/${projectId}/sites`, {
      method: "POST",
      body: JSON.stringify({ name, geometry: all.features[0].geometry }),
    });
    draw.current.deleteAll();
    setName("");
    setDrawing(false);
    onSaved();
  }

  return (
    <div className="map-wrap">
      <div ref={ref} className="map" />
      {drawing && (
        <div className="draw-box">
          <input
            placeholder="Site name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button onClick={save}>Save Site</button>
          <button
            className="secondary"
            onClick={() => {
              draw.current.deleteAll();
              setDrawing(false);
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

function App() {
  const [logged, setLogged] = useState(!!localStorage.getItem("token"));
  const [projects, setProjects] = useState([]);
  const [project, setProject] = useState(null);
  const [sites, setSites] = useState([]);
  const [selected, setSelected] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [newProject, setNewProject] = useState("");

  async function loadProjects() {
    const p = await request("/projects");
    setProjects(p);
    if (p.length && !project) setProject(p[0]);
  }

  async function loadSites() {
    if (!project) return;
    setSites(await request(`/projects/${project.id}/sites`));
  }

  useEffect(() => {
    if (logged) loadProjects().catch(() => setLogged(false));
  }, [logged]);
  useEffect(() => {
    loadSites();
  }, [project]);

  async function selectSite(site) {
    setSelected(site);
    setMetrics(await request(`/sites/${site.id}/analytics`));
  }

  async function createProject() {
    if (!newProject.trim()) return;
    await request("/projects", {
      method: "POST",
      body: JSON.stringify({ name: newProject }),
    });
    setNewProject("");
    loadProjects();
  }

  if (!logged) return <Auth onLogin={() => setLogged(true)} />;

  return (
    <div className="app">
      <header>
        <div className="brand">
          Darukaa<span>.Earth</span>
        </div>
        <div className="header-actions">
          <span>Environmental Intelligence</span>
          <button
            className="secondary"
            onClick={() => {
              localStorage.removeItem("token");
              setLogged(false);
            }}
          >
            Logout
          </button>
        </div>
      </header>
      <main>
        <aside>
          <div className="section-title">Projects</div>
          {projects.map((p) => (
            <button
              key={p.id}
              className={`project-btn ${project?.id === p.id ? "active" : ""}`}
              onClick={() => {
                setProject(p);
                setSelected(null);
              }}
            >
              {p.name}
              <small>{p.site_count} sites</small>
            </button>
          ))}
          <div className="new-project">
            <input
              placeholder="New project"
              value={newProject}
              onChange={(e) => setNewProject(e.target.value)}
            />
            <button onClick={createProject}>+</button>
          </div>
        </aside>
        <section className="content">
          <div className="top">
            <div>
              <h1>{project?.name || "Projects"}</h1>
              <p>
                {project?.description ||
                  "Manage geographic sites and environmental performance."}
              </p>
            </div>
            <div className="stats">
              <div>
                <b>{sites.length}</b>
                <span>Sites</span>
              </div>
              <div>
                <b>245 ha</b>
                <span>Tracked area</span>
              </div>
              <div>
                <b>84</b>
                <span>Eco score</span>
              </div>
            </div>
          </div>

          {project && (
            <MapPanel
              projectId={project.id}
              sites={sites}
              onSaved={loadSites}
              onSelect={selectSite}
            />
          )}

          {selected && (
            <div className="analytics">
              <div className="analytics-head">
                <div>
                  <h2>{selected.name}</h2>
                  <p>Site performance over time</p>
                </div>
                <div className="pill">{selected.status}</div>
              </div>
              <div className="cards">
                <div>
                  <span>Carbon</span>
                  <b>{metrics.at(-1)?.carbon ?? "--"} tCO₂e</b>
                </div>
                <div>
                  <span>Biodiversity</span>
                  <b>{metrics.at(-1)?.biodiversity ?? "--"} / 100</b>
                </div>
                <div>
                  <span>Soil Health</span>
                  <b>{metrics.at(-1)?.soil ?? "--"} / 100</b>
                </div>
                <div>
                  <span>Water</span>
                  <b>{metrics.at(-1)?.water ?? "--"} / 100</b>
                </div>
              </div>
              <div className="chart-card">
                <h3>Performance Trend</h3>
                <Line
                  data={{
                    labels: metrics.map((m) => m.date),
                    datasets: [
                      {
                        label: "Carbon",
                        data: metrics.map((m) => m.carbon),
                        tension: 0.35,
                      },
                      {
                        label: "Biodiversity",
                        data: metrics.map((m) => m.biodiversity),
                        tension: 0.35,
                      },
                      {
                        label: "Habitat",
                        data: metrics.map((m) => m.habitat),
                        tension: 0.35,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    plugins: { legend: { position: "bottom" } },
                  }}
                />
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
