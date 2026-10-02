import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Database,
  FileWarning,
  Globe2,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  Menu,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  X,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API = "https://fssai-rms.onrender.com";
type FdaSummary = {
  total_refusal_events: number;
  unique_countries: number;
  unique_industry_codes: number;
  unique_charge_categories: number;
  earliest_refusal_date: string;
  latest_refusal_date: string;
};

type EuSummary = {
  total_events: number;
  unique_origins: number;
  unique_notifying_countries: number;
  earliest_event_date: string;
  latest_event_date: string;
  serious_events: number;
  events_with_hazards: number;
};

type IndiaSummary = {
  jurisdiction: string;
  regulator: string;
  stage: string;
  total_rows: number;
  total_rejection_count: number;
  total_countries: number;
  financial_years: string[];
};

type FdaEvent = {
  id: number;
  refusal_id?: string;
  entry_num?: string;
  line_num?: string;
  refusal_date?: string;
  product_code?: string;
  industry_code?: string;
  food_class?: string;
  product_desc?: string;
  country_code?: string;
  country_name?: string;
  manufacturer_name?: string;
  manufacturer_city?: string;
  port_of_entry?: string;
  primary_charge_code?: string;
  primary_act_section?: string;
  primary_charge_statement?: string;
  charge_category?: string;
  defect_standard_status?: string;
};

type EuEvent = {
  id: number;
  reference?: string;
  category?: string;
  type?: string;
  subject?: string;
  event_date?: string;
  event_year?: number;
  event_timestamp?: string;
  notifying_country?: string;
  classification?: string;
  risk_decision?: string;
  distribution?: string;
  for_attention?: string;
  for_follow_up?: string;
  operator?: string;
  origin?: string;
  primary_origin_country?: string;
  hazards_raw?: string;
  primary_hazard_substance?: string;
  primary_hazard_category?: string;
  has_multiple_hazards?: number;
  food_class_scope?: string;
};

type IndiaRecord = {
  id: number;
  financial_year?: string;
  country_of_origin?: string;
  rejection_count?: number;
  rejected_items?: string;
  source_file?: string;
  stage?: string;
};

function displayField(val: string | number | undefined | null): string {
  if (val === null || val === undefined) return "Not specified";
  const str = String(val).trim();
  return str === "" ? "Not specified" : str;
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("sentra_token"));
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [fdaSummary, setFdaSummary] = useState<FdaSummary | null>(null);
  const [euSummary, setEuSummary] = useState<EuSummary | null>(null);
  const [indiaSummary, setIndiaSummary] = useState<IndiaSummary | null>(null);
  const [fdaIndiaCount, setFdaIndiaCount] = useState<number>(0);

  const [fdaEvents, setFdaEvents] = useState<FdaEvent[]>([]);
  const [fdaTotal, setFdaTotal] = useState(0);
  const [fdaPage, setFdaPage] = useState(1);
  const [fdaTotalPages, setFdaTotalPages] = useState(1);
  const [fdaSearch, setFdaSearch] = useState("");
  const [fdaCountryFilter, setFdaCountryFilter] = useState("");
  const [fdaIndustryFilter, setFdaIndustryFilter] = useState("");
  const [fdaFilters, setFdaFilters] = useState<{ industry_codes: string[] }>({ industry_codes: [] });

  const [euEvents, setEuEvents] = useState<EuEvent[]>([]);
  const [euTotal, setEuTotal] = useState(0);
  const [euPage, setEuPage] = useState(1);
  const [euTotalPages, setEuTotalPages] = useState(1);
  const [euSearch, setEuSearch] = useState("");

  const [indiaRecords, setIndiaRecords] = useState<IndiaRecord[]>([]);
  const [indiaTotal, setIndiaTotal] = useState(0);
  const [indiaPage, setIndiaPage] = useState(1);
  const [indiaTotalPages, setIndiaTotalPages] = useState(1);

  const [activeNav, setActiveNav] = useState("overview-india");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedFda, setSelectedFda] = useState<FdaEvent | null>(null);
  const [selectedEu, setSelectedEu] = useState<EuEvent | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") {
      setSelectedFda(null);
      setSelectedEu(null);
    }
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const response = await axios.post(`${API}/api/auth/login`, { username, password });
      const newToken = response.data.access_token;
      localStorage.setItem("sentra_token", newToken);
      setToken(newToken);
      setPassword("");
    } catch {
      setError("Invalid username or password.");
    }
  }

  function logout() {
    localStorage.removeItem("sentra_token");
    setToken(null);
    setSelectedFda(null);
    setSelectedEu(null);
  }

  async function loadSummaries() {
    if (!token) return;
    try {
      const [fdaRes, euRes, indRes, filterRes, fdaInRes] = await Promise.all([
        axios.get(`${API}/api/fda/summary`, { headers }),
        axios.get(`${API}/api/eu/summary`, { headers }),
        axios.get(`${API}/api/india/rejections/summary`, { headers }),
        axios.get(`${API}/api/fda/filters`, { headers }),
        axios.get(`${API}/api/fda/events?country_code=IN&page=1&page_size=10`, { headers }),
      ]);
      setFdaSummary(fdaRes.data);
      setEuSummary(euRes.data);
      setIndiaSummary(indRes.data);
      setFdaFilters(filterRes.data);
      setFdaIndiaCount(fdaInRes.data.total);
    } catch (err: any) {
      if (err.response?.status === 401) logout();
    }
  }

  async function loadFdaEvents() {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(fdaPage), page_size: "10" });
      if (fdaSearch.trim()) params.set("search", fdaSearch.trim());
      if (fdaCountryFilter) params.set("country_code", fdaCountryFilter);
      if (fdaIndustryFilter) params.set("industry_code", fdaIndustryFilter);

      const res = await axios.get(`${API}/api/fda/events?${params.toString()}`, { headers });
      setFdaEvents(res.data.items);
      setFdaTotalPages(res.data.total_pages);
      setFdaTotal(res.data.total);
    } catch (err: any) {
      if (err.response?.status === 401) logout();
    } finally {
      setLoading(false);
    }
  }

  async function loadEuEvents() {
    if (!token) return;
    try {
      const params = new URLSearchParams({ page: String(euPage), page_size: "10" });
      if (euSearch.trim()) params.set("search", euSearch.trim());
      const res = await axios.get(`${API}/api/eu/events?${params.toString()}`, { headers });
      setEuEvents(res.data.items);
      setEuTotalPages(res.data.total_pages);
      setEuTotal(res.data.total);
    } catch (err: any) {
      if (err.response?.status === 401) logout();
    }
  }

  async function loadIndiaRecords() {
    if (!token) return;
    try {
      const res = await axios.get(`${API}/api/india/rejections/records?page=${indiaPage}&page_size=10`, { headers });
      setIndiaRecords(res.data.items);
      setIndiaTotalPages(res.data.total_pages);
      setIndiaTotal(res.data.total);
    } catch (err: any) {
      if (err.response?.status === 401) logout();
    }
  }

  useEffect(() => {
    if (token) {
      loadSummaries();
      loadFdaEvents();
      loadEuEvents();
      loadIndiaRecords();
    }
  }, [token]);

  useEffect(() => {
    if (token) loadFdaEvents();
  }, [fdaPage, fdaCountryFilter, fdaIndustryFilter]);

  useEffect(() => {
    if (token) loadEuEvents();
  }, [euPage]);

  useEffect(() => {
    if (token) loadIndiaRecords();
  }, [indiaPage]);

  if (!token) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="brand-mark"><ShieldCheck size={26} /></div>
          <div className="login-brand">SENTRA-FS</div>
          <p className="login-subtitle">Food Safety Regulatory Intelligence & Risk Monitoring Platform</p>
          <form className="login-form" onSubmit={login}>
            <label>Username</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} required />
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            {error && <div className="login-error">{error}</div>}
            <button type="submit">Sign In to Regulatory Terminal</button>
          </form>
        </div>
      </div>
    );
  }

  const sampleChartData = fdaEvents.reduce((acc: { country: string; count: number }[], item) => {
    const code = item.country_code || "Unknown";
    const existing = acc.find((x) => x.country === code);
    if (existing) existing.count++;
    else acc.push({ country: code, count: 1 });
    return acc;
  }, []).sort((a, b) => b.count - a.count);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "" : "collapsed"}`}>
        <div className="sidebar-header">
          <div className="brand-icon"><ShieldCheck size={20} /></div>
          {sidebarOpen && (
            <div>
              <div className="brand-title">SENTRA-FS</div>
              <div className="brand-caption">FOOD SAFETY INTELLIGENCE</div>
            </div>
          )}
        </div>
        <nav>
          <div className="nav-section">OVERVIEW</div>
          <button className={`nav-item ${activeNav === "overview-india" ? "active" : ""}`} onClick={() => setActiveNav("overview-india")}>
            <LayoutDashboard size={16} />{sidebarOpen && "Dashboard Overview"}
          </button>
          <div className="nav-section">INVESTIGATION</div>
          <button className={`nav-item ${activeNav === "monitoring-refusals" ? "active" : ""}`} onClick={() => setActiveNav("monitoring-refusals")}>
            <FileWarning size={16} />{sidebarOpen && "FDA Refusals"}
          </button>
          <button className={`nav-item ${activeNav === "investigation-eu" ? "active" : ""}`} onClick={() => setActiveNav("investigation-eu")}>
            <Globe2 size={16} />{sidebarOpen && "EU RASFF Events"}
          </button>
          <button className={`nav-item ${activeNav === "investigation-fira" ? "active" : ""}`} onClick={() => setActiveNav("investigation-fira")}>
            <Database size={16} />{sidebarOpen && "India FIRA Records"}
          </button>
        </nav>
        <div className="sidebar-bottom">
          <button className="nav-item logout" onClick={logout}>
            <LogOut size={16} />{sidebarOpen && "Sign out"}
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="icon-button" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <div className="topbar-title">
            <span>SENTRA-FS</span>
            <small>Integrated Regulatory Import Safety Terminal</small>
          </div>
          <div className="topbar-right">
            <span className="status-dot" /> SYSTEM OPERATIONAL
          </div>
        </header>

        <section className="content">
          <div className="page-heading">
            <div>
              <h1>Multi-Jurisdiction Safety Intelligence</h1>
              <p>Harmonized monitoring for US FDA OASIS, EU RASFF, and FSSAI FIRA lab rejections.</p>
            </div>
            <button className="refresh-button" onClick={() => { loadSummaries(); loadFdaEvents(); loadEuEvents(); loadIndiaRecords(); }} disabled={loading}>
              <RefreshCw size={13} className={loading ? "spin" : ""} /> Refresh Feeds
            </button>
          </div>

          {/* Top Primary Metrics */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon"><FileWarning size={18} /></div>
              <div>
                <span>FDA Total Refusals</span>
                <strong>{fdaSummary?.total_refusal_events?.toLocaleString() ?? "—"}</strong>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon"><Globe2 size={18} /></div>
              <div>
                <span>FDA Monitored Origins</span>
                <strong>{fdaSummary?.unique_countries ?? "—"}</strong>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon"><BarChart3 size={18} /></div>
              <div>
                <span>FDA Industry Categories</span>
                <strong>{fdaSummary?.unique_industry_codes ?? "—"}</strong>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon"><Activity size={18} /></div>
              <div>
                <span>FDA Date Coverage</span>
                <strong>
                  {fdaSummary ? `${fdaSummary.earliest_refusal_date.slice(0, 4)}–${fdaSummary.latest_refusal_date.slice(0, 4)}` : "—"}
                </strong>
              </div>
            </div>
          </div>

          {/* Database-Driven Aggregates */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Verified Regulatory Intelligence Aggregates</h2>
                <span>Exact empirical records queried directly from local database stores</span>
              </div>
            </div>
            <div style={{ padding: "16px 18px" }}>
              <div className="stats-grid" style={{ marginBottom: 0 }}>
                <div className="stat-card">
                  <div className="stat-icon"><FileWarning size={18} /></div>
                  <div>
                    <span>FDA refusals involving India</span>
                    <strong>{fdaIndiaCount.toLocaleString()}</strong>
                    <small style={{ color: "#718096", fontSize: "11px" }}>U.S. FDA OASIS notices for origin 'IN'</small>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon"><ShieldCheck size={18} /></div>
                  <div>
                    <span>FIRA aggregate records</span>
                    <strong>{indiaSummary?.total_rows ?? "—"}</strong>
                    <small style={{ color: "#718096", fontSize: "11px" }}>FSSAI laboratory testing aggregate rows</small>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon"><ShieldAlert size={18} /></div>
                  <div>
                    <span>Reported rejection events</span>
                    <strong>{indiaSummary?.total_rejection_count?.toLocaleString() ?? "—"}</strong>
                    <small style={{ color: "#718096", fontSize: "11px" }}>Summed FSSAI/FIRA rejection volume</small>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon"><Globe2 size={18} /></div>
                  <div>
                    <span>RASFF border events</span>
                    <strong>{euSummary?.total_events?.toLocaleString() ?? "—"}</strong>
                    <small style={{ color: "#718096", fontSize: "11px" }}>European Commission active database rows</small>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Connected Feeds Table */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <h2>Global Surveillance Status</h2>
                <span>Cross-border food safety surveillance authorities and local integration status</span>
              </div>
            </div>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Jurisdiction</th>
                    <th>Authority / Source Feed</th>
                    <th>Integration Status</th>
                    <th>Records</th>
                    <th>Coverage / Scope</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: 650 }}>United States Refusal Intelligence</td>
                    <td>U.S. FDA Import Refusals (OASIS)</td>
                    <td>
                      <span className="country-badge" style={{ background: "#f0fdf4", color: "#166534" }}>
                        <CheckCircle2 size={10} style={{ marginRight: 4 }} /> Connected
                      </span>
                    </td>
                    <td style={{ fontFamily: "monospace" }}>{fdaSummary?.total_refusal_events?.toLocaleString() ?? "—"}</td>
                    <td>{fdaSummary ? `${fdaSummary.earliest_refusal_date} to ${fdaSummary.latest_refusal_date}` : "—"}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 650 }}>European Union Safety Gate</td>
                    <td>EC Rapid Alert System for Food and Feed (RASFF)</td>
                    <td>
                      <span className="country-badge" style={{ background: "#f0fdf4", color: "#166534" }}>
                        <CheckCircle2 size={10} style={{ marginRight: 4 }} /> Connected
                      </span>
                    </td>
                    <td style={{ fontFamily: "monospace" }}>{euSummary?.total_events?.toLocaleString() ?? "—"}</td>
                    <td>{euSummary ? `${euSummary.earliest_event_date} to ${euSummary.latest_event_date}` : "—"}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 650 }}>India Regulatory Registry</td>
                    <td>FSSAI / FIRA Domestic Intelligence</td>
                    <td>
                      <span className="country-badge" style={{ background: "#f0fdf4", color: "#166534" }}>
                        <CheckCircle2 size={10} style={{ marginRight: 4 }} /> Connected
                      </span>
                    </td>
                    <td style={{ fontFamily: "monospace" }}>{indiaSummary ? `${indiaSummary.total_rows} rows (${indiaSummary.total_rejection_count} rejections)` : "—"}</td>
                    <td>{indiaSummary?.financial_years?.join(", ") ?? "—"}</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 650 }}>Australia Biosecurity Import System</td>
                    <td>DAFF Imported Food Inspection Scheme</td>
                    <td>
                      <span className="country-badge" style={{ background: "#fafaf9", color: "#78716c" }}>
                        <HelpCircle size={10} style={{ marginRight: 4 }} /> Pending
                      </span>
                    </td>
                    <td>—</td>
                    <td>Awaiting Feed</td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 650 }}>Canada Food Inspection Intelligence</td>
                    <td>CFIA Automated Import Reference</td>
                    <td>
                      <span className="country-badge" style={{ background: "#fafaf9", color: "#78716c" }}>
                        <HelpCircle size={10} style={{ marginRight: 4 }} /> Pending
                      </span>
                    </td>
                    <td>—</td>
                    <td>Awaiting Feed</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Conditional Workspaces / Investigation Tables */}
          {activeNav === "overview-india" && (
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Active Investigation Sample (Current Page)</h2>
                  <span>Country origin distribution of current FDA search sample</span>
                </div>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={sampleChartData.slice(0, 10)}>
                    <CartesianGrid vertical={false} />
                    <XAxis dataKey="country" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#173b5f" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* FDA Refusals Investigation Table */}
          {(activeNav === "overview-india" || activeNav === "monitoring-refusals") && (
            <div className="panel" id="fda-table">
              <div className="panel-header">
                <div>
                  <h2>U.S. FDA Import Refusals</h2>
                  <span>Empirical OASIS records • Click any row to view complete statutory dossier</span>
                </div>
                <span style={{ fontSize: "12px", color: "#718096" }}>{fdaTotal.toLocaleString()} records matched</span>
              </div>
              <form className="filters" onSubmit={(e) => { e.preventDefault(); setFdaPage(1); loadFdaEvents(); }}>
                <div className="search-box">
                  <Search size={14} />
                  <input value={fdaSearch} onChange={(e) => setFdaSearch(e.target.value)} placeholder="Search product, manufacturer, charges..." />
                </div>
                <select value={fdaCountryFilter} onChange={(e) => { setFdaCountryFilter(e.target.value); setFdaPage(1); }}>
                  <option value="">All Origins</option>
                  <option value="IN">India (IN)</option>
                  <option value="CN">China (CN)</option>
                  <option value="MX">Mexico (MX)</option>
                </select>
                <select value={fdaIndustryFilter} onChange={(e) => { setFdaIndustryFilter(e.target.value); setFdaPage(1); }}>
                  <option value="">All Industry Codes</option>
                  {fdaFilters.industry_codes.map((item) => (
                    <option key={item} value={item}>Industry {item}</option>
                  ))}
                </select>
                <button className="refresh-button" type="submit">Filter</button>
              </form>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Refusal ID</th>
                      <th>Refusal Date</th>
                      <th>Origin</th>
                      <th>Commodity / Product</th>
                      <th>Industry</th>
                      <th>Manufacturer</th>
                      <th>Charge Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fdaEvents.map((ev) => (
                      <tr key={ev.id} onClick={() => setSelectedFda(ev)} style={{ cursor: "pointer" }}>
                        <td style={{ fontFamily: "monospace" }}>{displayField(ev.refusal_id || ev.id)}</td>
                        <td>{displayField(ev.refusal_date)}</td>
                        <td><span className="country-badge">{displayField(ev.country_code)}</span></td>
                        <td className="product-cell" title={ev.product_desc}>{displayField(ev.product_desc)}</td>
                        <td>{displayField(ev.industry_code)}</td>
                        <td>{displayField(ev.manufacturer_name)}</td>
                        <td><span className="country-badge">{displayField(ev.charge_category)}</span></td>
                      </tr>
                    ))}
                    {fdaEvents.length === 0 && (
                      <tr><td colSpan={7} style={{ textAlign: "center", padding: "20px" }}>No FDA refusal records found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="pagination">
                <button disabled={fdaPage <= 1} onClick={() => setFdaPage((p) => p - 1)}>Previous</button>
                <span>Page {fdaPage} of {fdaTotalPages || 1}</span>
                <button disabled={fdaPage >= fdaTotalPages} onClick={() => setFdaPage((p) => p + 1)}>Next</button>
              </div>
            </div>
          )}

          {/* EU RASFF Border Events Table */}
          {(activeNav === "overview-india" || activeNav === "investigation-eu") && (
            <div className="panel" id="eu-table">
              <div className="panel-header">
                <div>
                  <h2>European Union RASFF Border Events</h2>
                  <span>Connected EU border intervention database • Click any row for dossier</span>
                </div>
                <span style={{ fontSize: "12px", color: "#718096" }}>{euTotal.toLocaleString()} records matched</span>
              </div>
              <form className="filters" onSubmit={(e) => { e.preventDefault(); setEuPage(1); loadEuEvents(); }}>
                <div className="search-box">
                  <Search size={14} />
                  <input value={euSearch} onChange={(e) => setEuSearch(e.target.value)} placeholder="Search reference, subject, origin, hazard..." />
                </div>
                <button className="refresh-button" type="submit">Search</button>
              </form>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Reference</th>
                      <th>Event Date</th>
                      <th>Origin</th>
                      <th>Notifying Country</th>
                      <th>Subject</th>
                      <th>Classification</th>
                      <th>Risk Decision</th>
                      <th>Hazard</th>
                    </tr>
                  </thead>
                  <tbody>
                    {euEvents.map((item) => (
                      <tr key={item.id} onClick={() => setSelectedEu(item)} style={{ cursor: "pointer" }}>
                        <td style={{ fontFamily: "monospace" }}>{displayField(item.reference)}</td>
                        <td>{displayField(item.event_date)}</td>
                        <td><span className="country-badge">{displayField(item.origin || item.primary_origin_country)}</span></td>
                        <td>{displayField(item.notifying_country)}</td>
                        <td className="product-cell" title={item.subject}>{displayField(item.subject)}</td>
                        <td>{displayField(item.classification)}</td>
                        <td><span className="country-badge">{displayField(item.risk_decision)}</span></td>
                        <td>{displayField(item.primary_hazard_substance || item.hazards_raw)}</td>
                      </tr>
                    ))}
                    {euEvents.length === 0 && (
                      <tr><td colSpan={8} style={{ textAlign: "center", padding: "20px" }}>No EU border events found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="pagination">
                <button disabled={euPage <= 1} onClick={() => setEuPage((p) => p - 1)}>Previous</button>
                <span>Page {euPage} of {euTotalPages || 1}</span>
                <button disabled={euPage >= euTotalPages} onClick={() => setEuPage((p) => p + 1)}>Next</button>
              </div>
            </div>
          )}

          {/* India FSSAI / FIRA Lab Rejections Table */}
          {(activeNav === "overview-india" || activeNav === "investigation-fira") && (
            <div className="panel" id="india-table">
              <div className="panel-header">
                <div>
                  <h2>India FIRA Laboratory Rejection Registry</h2>
                  <span>FSSAI import inspection records and statutory testing lab determinations</span>
                </div>
                <span style={{ fontSize: "12px", color: "#718096" }}>{indiaTotal.toLocaleString()} aggregate rows</span>
              </div>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Record ID</th>
                      <th>Financial Year</th>
                      <th>Country of Origin</th>
                      <th>Rejection Count</th>
                      <th>Rejected Items / Commodity</th>
                      <th>Surveillance Stage</th>
                      <th>Source Document</th>
                    </tr>
                  </thead>
                  <tbody>
                    {indiaRecords.map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontFamily: "monospace" }}>{r.id}</td>
                        <td>{displayField(r.financial_year)}</td>
                        <td><span className="country-badge">{displayField(r.country_of_origin)}</span></td>
                        <td style={{ fontWeight: 700 }}>{displayField(r.rejection_count)}</td>
                        <td className="product-cell" title={r.rejected_items}>{displayField(r.rejected_items)}</td>
                        <td>{displayField(r.stage)}</td>
                        <td style={{ fontSize: "11px", color: "#718096" }}>{displayField(r.source_file)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="pagination">
                <button disabled={indiaPage <= 1} onClick={() => setIndiaPage((p) => p - 1)}>Previous</button>
                <span>Page {indiaPage} of {indiaTotalPages || 1}</span>
                <button disabled={indiaPage >= indiaTotalPages} onClick={() => setIndiaPage((p) => p + 1)}>Next</button>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* FDA Modal Drawer */}
      {selectedFda && (
        <div className="drawer-overlay" style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", justifyContent: "flex-end", backgroundColor: "rgba(18, 43, 68, 0.4)" }} onClick={() => setSelectedFda(null)}>
          <div style={{ width: "100%", maxWidth: "580px", height: "100%", background: "#fff", borderLeft: "1px solid #dce4eb", overflowY: "auto", padding: "20px" }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <ShieldAlert size={20} color="#173b5f" />
                <h3 style={{ margin: 0, fontSize: "15px" }}>FDA Refusal Dossier</h3>
              </div>
              <button className="icon-button" onClick={() => setSelectedFda(null)}><X size={18} /></button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px" }}>
              <div style={{ background: "#f8fafc", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#64748b", fontWeight: 700 }}>PRODUCT DESCRIPTION</p>
                <div style={{ fontWeight: 600 }}>{displayField(selectedFda.product_desc)}</div>
              </div>
              <p><strong>Refusal ID:</strong> {displayField(selectedFda.refusal_id || selectedFda.id)}</p>
              <p><strong>Entry / Line:</strong> {displayField(selectedFda.entry_num)} / {displayField(selectedFda.line_num)}</p>
              <p><strong>Refusal Date:</strong> {displayField(selectedFda.refusal_date)}</p>
              <p><strong>Origin Nation:</strong> {displayField(selectedFda.country_name)} ({displayField(selectedFda.country_code)})</p>
              <p><strong>Manufacturer:</strong> {displayField(selectedFda.manufacturer_name)}</p>
              <p><strong>Port of Entry:</strong> {displayField(selectedFda.port_of_entry)}</p>
              <hr style={{ border: 0, borderTop: "1px solid #e2e8f0", margin: "8px 0" }} />
              <div style={{ background: "#fef2f2", padding: "10px", borderRadius: "6px", border: "1px solid #fecaca" }}>
                <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#991b1b", fontWeight: 700 }}>STATUTORY VIOLATION / FINDING</p>
                <p style={{ margin: "4px 0" }}><strong>Act Section:</strong> {displayField(selectedFda.primary_act_section)}</p>
                <p style={{ margin: "4px 0" }}><strong>Charge Statement:</strong> {displayField(selectedFda.primary_charge_statement)}</p>
                <p style={{ margin: "4px 0" }}><strong>Charge Category:</strong> {displayField(selectedFda.charge_category)}</p>
                <p style={{ margin: "4px 0" }}><strong>Defect Standard Status:</strong> {displayField(selectedFda.defect_standard_status)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* EU RASFF Modal Drawer */}
      {selectedEu && (
        <div className="drawer-overlay" style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", justifyContent: "flex-end", backgroundColor: "rgba(18, 43, 68, 0.4)" }} onClick={() => setSelectedEu(null)}>
          <div style={{ width: "100%", maxWidth: "580px", height: "100%", background: "#fff", borderLeft: "1px solid #dce4eb", overflowY: "auto", padding: "20px" }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <ShieldAlert size={20} color="#173b5f" />
                <h3 style={{ margin: 0, fontSize: "15px" }}>EU RASFF Event Dossier</h3>
              </div>
              <button className="icon-button" onClick={() => setSelectedEu(null)}><X size={18} /></button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px" }}>
              <div style={{ background: "#f8fafc", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#64748b", fontWeight: 700 }}>NOTIFICATION SUBJECT</p>
                <div style={{ fontWeight: 600 }}>{displayField(selectedEu.subject)}</div>
              </div>
              <p><strong>Reference:</strong> {displayField(selectedEu.reference)}</p>
              <p><strong>Event Date:</strong> {displayField(selectedEu.event_date)} ({displayField(selectedEu.event_year)})</p>
              <p><strong>Origin Nation:</strong> {displayField(selectedEu.origin || selectedEu.primary_origin_country)}</p>
              <p><strong>Notifying Member State:</strong> {displayField(selectedEu.notifying_country)}</p>
              <p><strong>Classification:</strong> {displayField(selectedEu.classification)}</p>
              <p><strong>Risk Decision:</strong> {displayField(selectedEu.risk_decision)}</p>
              <hr style={{ border: 0, borderTop: "1px solid #e2e8f0", margin: "8px 0" }} />
              <div style={{ background: "#fef2f2", padding: "10px", borderRadius: "6px", border: "1px solid #fecaca" }}>
                <p style={{ margin: "0 0 4px", fontSize: "11px", color: "#991b1b", fontWeight: 700 }}>IDENTIFIED HAZARDS & VIOLATIONS</p>
                <p style={{ margin: "4px 0" }}><strong>Primary Hazard Substance:</strong> {displayField(selectedEu.primary_hazard_substance)}</p>
                <p style={{ margin: "4px 0" }}><strong>Hazard Category:</strong> {displayField(selectedEu.primary_hazard_category)}</p>
                <p style={{ margin: "4px 0" }}><strong>Raw Hazards Text:</strong> {displayField(selectedEu.hazards_raw)}</p>
                <p style={{ margin: "4px 0" }}><strong>Multiple Hazards Detected:</strong> {selectedEu.has_multiple_hazards ? "Yes" : "No"}</p>
              </div>
              <p><strong>Distribution Status:</strong> {displayField(selectedEu.distribution)}</p>
              <p><strong>Operator:</strong> {displayField(selectedEu.operator)}</p>
              <p><strong>Food Class Scope:</strong> {displayField(selectedEu.food_class_scope)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
