const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeader(serverToken?: string | null): Record<string, string> {
  if (serverToken) return { Authorization: `Bearer ${serverToken}` };
  if (typeof window !== "undefined") {
    const t = localStorage.getItem("auth_token");
    if (t) return { Authorization: `Bearer ${t}` };
  }
  return {};
}

export async function login(username: string, password: string): Promise<string> {
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  return data.access_token;
}

export interface Announcement {
  id: number;
  bid_number: string;
  title: string;
  organization: string;
  category: string | null;
  region: string | null;
  budget: number | null;
  deadline: string | null;
  source_url: string | null;
  status: string;
  dday: number | null;
  created_at: string;
}

export interface FilterConfig {
  id: number;
  name: string;
  keywords: string[] | null;
  categories: string[] | null;
  regions: string[] | null;
  organizations: string[] | null;
  budget_min: number | null;
  budget_max: number | null;
  notify_email: string | null;
  notify_slack: boolean;
  reminder_days: number[];
  active: boolean;
}

export interface AnnouncementQuery {
  keyword?: string;
  category?: string;
  region?: string;
  organization?: string;
  budget_min?: number;
  budget_max?: number;
  status?: string;
  deadline_before?: string;
  deadline_after?: string;
  page?: number;
  size?: number;
}

export async function fetchAnnouncements(
  query: AnnouncementQuery = {}
): Promise<{ data: Announcement[]; total: number }> {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([k, v]) => {
    if (v !== undefined && v !== "") params.set(k, String(v));
  });
  const res = await fetch(`${BASE}/api/v1/announcements?${params}`, {
    cache: "no-store",
  });
  const total = parseInt(res.headers.get("x-total-count") ?? "0", 10);
  const data = await res.json();
  return { data, total };
}

export async function fetchFilters(token?: string | null): Promise<FilterConfig[]> {
  const res = await fetch(`${BASE}/api/v1/filters`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function createFilter(
  body: Omit<FilterConfig, "id">
): Promise<FilterConfig> {
  const res = await fetch(`${BASE}/api/v1/filters`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function deleteFilter(id: number): Promise<void> {
  await fetch(`${BASE}/api/v1/filters/${id}`, {
    method: "DELETE",
    headers: authHeader(),
  });
}

export async function triggerCrawl(): Promise<void> {
  await fetch(`${BASE}/api/v1/announcements/crawl`, {
    method: "POST",
    headers: authHeader(),
  });
}

// ── Phase 2 types ────────────────────────────────────────────────────────────

export interface Company {
  id: number;
  name: string;
  business_number: string;
  ceo_name: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  business_types: string | null;
  active: boolean;
}

export interface BidDocument {
  id: number;
  application_id: number;
  doc_type: string;
  title: string;
  content: string;
  status: string;
  reviewer_note: string | null;
  reviewed_at: string | null;
  approved_at: string | null;
  submitted_at: string | null;
  created_at: string;
}

export interface BidApplication {
  id: number;
  announcement_id: number;
  company_id: number;
  status: string;
  required_docs: string[] | null;
  bid_price: number | null;
  notes: string | null;
  submitted_at: string | null;
  created_at: string;
  documents: BidDocument[];
  result: string | null;
  result_price: number | null;
  winner_price: number | null;
  our_rank: number | null;
  total_bidders: number | null;
  loss_reason: string | null;
}

// ── Phase 2 API ──────────────────────────────────────────────────────────────

export async function fetchCompanies(token?: string | null): Promise<Company[]> {
  const res = await fetch(`${BASE}/api/v1/companies`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function createCompany(body: Omit<Company, "id" | "active">): Promise<Company> {
  const res = await fetch(`${BASE}/api/v1/companies`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function fetchApplications(token?: string | null): Promise<BidApplication[]> {
  const res = await fetch(`${BASE}/api/v1/applications`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function fetchApplication(id: number, token?: string | null): Promise<BidApplication> {
  const res = await fetch(`${BASE}/api/v1/applications/${id}`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function createApplication(body: {
  announcement_id: number;
  company_id: number;
  bid_price?: number;
  notes?: string;
}): Promise<BidApplication> {
  const res = await fetch(`${BASE}/api/v1/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function submitApplication(id: number): Promise<BidApplication> {
  const res = await fetch(`${BASE}/api/v1/applications/${id}/submit`, {
    method: "POST",
    headers: authHeader(),
  });
  return res.json();
}

export async function reviewDocument(
  docId: number,
  action: "approve" | "reject",
  note?: string
): Promise<BidDocument> {
  const res = await fetch(`${BASE}/api/v1/documents/${docId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ action, note }),
  });
  return res.json();
}

export async function fetchDocument(docId: number, token?: string | null): Promise<BidDocument> {
  const res = await fetch(`${BASE}/api/v1/documents/${docId}`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

// ── Phase 3 types ────────────────────────────────────────────────────────────

export interface AwardStats {
  count: number;
  mean: number;
  median: number;
  p10: number;
  p25: number;
  p75: number;
  p90: number;
  min: number;
  max: number;
  distribution: Record<string, number>;
  category: string | null;
}

export interface RecommendResult {
  predicted_rate: number;
  recommended_range: { low: number; high: number };
  recommended_price_low: number;
  recommended_price_high: number;
  model_version: string | null;
  model_mae: number | null;
}

export interface SimulationScenario {
  rate: number;
  rate_pct: string;
  bid_price: number;
  win_prob: number;
  win_prob_pct: string;
  margin_rate: number | null;
  margin_amount: number | null;
}

export interface SimulationResult {
  scenarios: SimulationScenario[];
  optimal: SimulationScenario;
  data_count: number;
  category: string | null;
}

export interface MarginResult {
  base_price: number;
  bid_price: number;
  direct_cost: number;
  overhead: number;
  total_cost: number;
  margin: number;
  margin_rate: number;
  award_rate: number;
  is_profitable: boolean;
}

// ── Phase 3 API ──────────────────────────────────────────────────────────────

export async function fetchAwardStats(category?: string): Promise<AwardStats> {
  const p = category ? `?category=${encodeURIComponent(category)}` : "";
  const res = await fetch(`${BASE}/api/v1/price/stats${p}`, { cache: "no-store" });
  return res.json();
}

export async function fetchRecommend(params: {
  base_price: number;
  category?: string;
  region?: string;
  bid_count?: number;
}): Promise<RecommendResult> {
  const p = new URLSearchParams();
  p.set("base_price", String(params.base_price));
  if (params.category) p.set("category", params.category);
  if (params.region) p.set("region", params.region);
  if (params.bid_count) p.set("bid_count", String(params.bid_count));
  const res = await fetch(`${BASE}/api/v1/price/recommend?${p}`, { cache: "no-store" });
  return res.json();
}

export async function fetchSimulation(params: {
  base_price: number;
  category?: string;
  cost?: number;
}): Promise<SimulationResult> {
  const p = new URLSearchParams();
  p.set("base_price", String(params.base_price));
  if (params.category) p.set("category", params.category);
  if (params.cost) p.set("cost", String(params.cost));
  const res = await fetch(`${BASE}/api/v1/price/simulate?${p}`, { cache: "no-store" });
  return res.json();
}

export async function fetchMargin(params: {
  base_price: number;
  bid_price: number;
  cost: number;
  overhead_rate?: number;
}): Promise<MarginResult> {
  const p = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]));
  const res = await fetch(`${BASE}/api/v1/price/margin?${p}`, { cache: "no-store" });
  return res.json();
}

// ── Phase 4 types ────────────────────────────────────────────────────────────

export interface DashboardSummary {
  total_applications: number;
  submitted: number;
  won: number;
  lost: number;
  pending: number;
  win_rate: number;       // 0-100
  bid_amount: number;
  award_amount: number;
}

export interface MonthlyStats {
  month: string;
  submitted: number;
  won: number;
  lost: number;
  win_rate: number;       // 0-100
  award_amount: number;
}

export interface OrgStats {
  organization: string;
  submitted: number;
  won: number;
  win_rate: number;       // 0-100
  award_amount: number;
}

export interface CategoryStats {
  category: string;
  submitted: number;
  won: number;
  win_rate: number;       // 0-100
  award_amount: number;
}

export interface LossRecord {
  id: number;
  title: string;
  organization: string;
  our_bid_price: number | null;
  winner_price: number | null;
  our_rank: number | null;
  total_bidders: number | null;
  loss_reason: string | null;
  price_diff_pct: number | null;
}

export interface ResultUpdate {
  result: "won" | "lost";
  result_price?: number;
  winner_price?: number;
  our_rank?: number;
  total_bidders?: number;
}

// ── Phase 4 API ──────────────────────────────────────────────────────────────

export async function fetchDashboardSummary(token?: string | null): Promise<DashboardSummary> {
  const res = await fetch(`${BASE}/api/v1/dashboard/summary`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function fetchMonthlyStats(months = 12, token?: string | null): Promise<MonthlyStats[]> {
  const res = await fetch(`${BASE}/api/v1/dashboard/monthly?months=${months}`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function fetchByOrg(token?: string | null): Promise<OrgStats[]> {
  const res = await fetch(`${BASE}/api/v1/dashboard/by-org`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function fetchByCategory(token?: string | null): Promise<CategoryStats[]> {
  const res = await fetch(`${BASE}/api/v1/dashboard/by-category`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function fetchLossAnalysis(token?: string | null): Promise<LossRecord[]> {
  const res = await fetch(`${BASE}/api/v1/dashboard/loss-analysis`, {
    cache: "no-store",
    headers: authHeader(token),
  });
  return res.json();
}

export async function updateApplicationResult(
  appId: number,
  body: ResultUpdate
): Promise<{ id: number; result: string; loss_reason: string | null; result_updated_at: string | null }> {
  const res = await fetch(`${BASE}/api/v1/applications/${appId}/result`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function downloadExport(type: "csv" | "excel"): Promise<void> {
  const ext = type === "csv" ? "csv" : "xlsx";
  const res = await fetch(`${BASE}/api/v1/export/${type}`, {
    headers: authHeader(),
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `bidding_results.${ext}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 100);
}

// ── Phase 3 admin ─────────────────────────────────────────────────────────────

export async function triggerCollect(): Promise<{ collected: number }> {
  const res = await fetch(`${BASE}/api/v1/price/collect`, {
    method: "POST",
    headers: authHeader(),
  });
  return res.json();
}

export async function triggerTrain(category?: string): Promise<Record<string, unknown>> {
  const p = category ? `?category=${encodeURIComponent(category)}` : "";
  const res = await fetch(`${BASE}/api/v1/price/train${p}`, {
    method: "POST",
    headers: authHeader(),
  });
  return res.json();
}
