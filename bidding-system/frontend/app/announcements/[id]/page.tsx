import { fetchBidScore } from "@/lib/api";
import { getServerToken } from "@/lib/server-auth";
import AutoSetupPanel from "./AutoSetupPanel";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchAnn(id: number, token: string | null) {
  const res = await fetch(BASE + "/api/v1/announcements/" + id, {
    cache: "no-store",
    headers: token ? { Authorization: "Bearer " + token } : {},
  });
  if (!res.ok) return null;
  return res.json();
}

function fmtBudget(v: number | null) {
  if (!v) return "-";
  if (v >= 100_000_000) return (v / 100_000_000).toFixed(1) + "억원";
  if (v >= 10_000) return (v / 10_000).toFixed(0) + "만원";
  return v.toLocaleString() + "원";
}

function fmtDate(s: string | null) {
  if (!s) return "-";
  return new Date(s).toLocaleDateString("ko-KR");
}

const REC_STYLE: Record<string, string> = {
  bid: "bg-green-100 text-green-800 border-green-200",
  caution: "bg-yellow-100 text-yellow-800 border-yellow-200",
  pass: "bg-red-100 text-red-800 border-red-200",
};

export default async function AnnouncementDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const annId = Number(id);
  const token = await getServerToken();

  const [ann, bidScore] = await Promise.all([
    fetchAnn(annId, token),
    token ? fetchBidScore(annId, token).catch(() => null) : Promise.resolve(null),
  ]);

  if (!ann) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-8">
        <p className="text-gray-400">공고를 찾을 수 없습니다.</p>
        <a href="/" className="text-blue-600 text-sm hover:underline mt-2 inline-block">← 목록으로</a>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center gap-3">
        <a href="/" className="text-sm text-gray-400 hover:text-blue-600">← 공고 목록</a>
        {ann.dday !== null && (
          <span className={"text-xs font-semibold px-2 py-0.5 rounded-full " + (ann.dday <= 3 ? "bg-red-100 text-red-700" : ann.dday <= 7 ? "bg-amber-100 text-amber-700" : "bg-blue-100 text-blue-700")}>
            {ann.dday < 0 ? "마감" : ann.dday === 0 ? "D-Day" : "D-" + ann.dday}
          </span>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div>
          {ann.category && <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded mr-2">{ann.category}</span>}
          {ann.region && <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{ann.region}</span>}
        </div>
        <h1 className="text-xl font-bold text-gray-900">{ann.title}</h1>
        <p className="text-gray-600">{ann.organization}</p>
        {ann.ministry && ann.ministry !== ann.organization && <p className="text-sm text-gray-400">공고기관: {ann.ministry}</p>}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-100 text-sm">
          <div><span className="text-gray-400">예산</span><p className="font-semibold mt-0.5">{fmtBudget(ann.budget)}</p></div>
          <div><span className="text-gray-400">마감일</span><p className="font-semibold mt-0.5">{fmtDate(ann.deadline)}</p></div>
          <div><span className="text-gray-400">입찰방법</span><p className="font-semibold mt-0.5">{ann.support_type ?? "-"}</p></div>
          <div><span className="text-gray-400">공고번호</span><p className="font-semibold mt-0.5 text-xs">{ann.bid_number}</p></div>
        </div>
        {ann.eligible_institutions?.length > 0 && <div className="text-sm"><span className="text-gray-400">참가자격: </span><span>{ann.eligible_institutions.join(", ")}</span></div>}
        {ann.description && <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">{ann.description}</p>}
        {ann.source_url && <a href={ann.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800">나라장터 원문 보기 →</a>}
      </div>

      {token ? (
        <AutoSetupPanel annId={annId} />
      ) : (
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 text-center text-sm text-gray-500">
          <a href="/login" className="text-blue-600 hover:underline">로그인</a>하면 원클릭 자동 분석을 사용할 수 있습니다.
        </div>
      )}

      {bidScore ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">입찰 가부 판단</h2>
            <div className="flex items-center gap-2">
              {(bidScore as { needs_expert_review?: boolean }).needs_expert_review && (
                <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">⚠️ 전문가 검토 권장</span>
              )}
              <span className={"text-sm font-bold px-3 py-1 rounded-full border " + (REC_STYLE[bidScore.recommendation] ?? "")}>{bidScore.recommendation_label}</span>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1"><span>종합 점수</span><span className="font-semibold text-gray-800">{bidScore.overall} / {bidScore.max}</span></div>
            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className={"h-full rounded-full " + (bidScore.recommendation === "bid" ? "bg-green-500" : bidScore.recommendation === "caution" ? "bg-amber-400" : "bg-red-400")} style={{ width: bidScore.overall + "%" }} />
            </div>
          </div>
          <div className="space-y-2">
            {Object.values(bidScore.breakdown ?? {}).map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-24 shrink-0">{item.label}</span>
                <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-400 rounded-full" style={{ width: ((item.score / item.max) * 100) + "%" }} />
                </div>
                <span className="text-xs text-gray-600 tabular-nums w-12 text-right">{item.score}/{item.max}</span>
              </div>
            ))}
          </div>
          <ul className="space-y-1">{bidScore.reasoning.map((r: string, i: number) => <li key={i} className="text-xs text-gray-500 flex gap-1.5"><span className="text-gray-300">•</span>{r}</li>)}</ul>
          <a href="/applications" className="block w-full text-center bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700">입찰 지원 시작 →</a>
        </div>
      ) : null}
    </main>
  );
}
