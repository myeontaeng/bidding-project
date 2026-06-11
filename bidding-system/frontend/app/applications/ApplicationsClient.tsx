"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { BidApplication, Company, Announcement, createApplication } from "@/lib/api";

export const STATUS_LABEL: Record<string, { label: string; cls: string }> = {
  pending:     { label: "대기",     cls: "bg-gray-100 text-gray-600" },
  in_progress: { label: "진행중",   cls: "bg-blue-100 text-blue-700" },
  rejected:    { label: "서류반려", cls: "bg-orange-100 text-orange-700" },
  submitted:   { label: "제출완료", cls: "bg-green-100 text-green-700" },
  cancelled:   { label: "취소",     cls: "bg-gray-100 text-gray-400" },
  won:         { label: "낙찰",     cls: "bg-yellow-100 text-yellow-700" },
  lost:        { label: "유찰",     cls: "bg-red-100 text-red-600" },
};

const FILTER_OPTIONS = [
  { value: "", label: "전체" },
  { value: "in_progress", label: "진행중" },
  { value: "rejected", label: "서류반려" },
  { value: "submitted", label: "제출완료" },
  { value: "won", label: "낙찰" },
  { value: "lost", label: "유찰" },
  { value: "cancelled", label: "취소" },
];

interface Props {
  initialApplications: BidApplication[];
  companies: Company[];
  announcements: Announcement[];
}

export default function ApplicationsClient({ initialApplications, companies, announcements }: Props) {
  const router = useRouter();
  const [apps, setApps] = useState(initialApplications);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ announcement_id: 0, company_id: 0, bid_price: "", notes: "" });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // 검색 / 필터
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const filtered = useMemo(() => {
    let list = apps;
    if (statusFilter) list = list.filter((a) => a.status === statusFilter);
    if (keyword.trim()) {
      const kw = keyword.trim().toLowerCase();
      list = list.filter((a) => {
        const ann = announcements.find((x) => x.id === a.announcement_id);
        const co = companies.find((x) => x.id === a.company_id);
        return (
          ann?.title?.toLowerCase().includes(kw) ||
          ann?.organization?.toLowerCase().includes(kw) ||
          co?.name?.toLowerCase().includes(kw) ||
          a.notes?.toLowerCase().includes(kw)
        );
      });
    }
    return list;
  }, [apps, keyword, statusFilter, announcements, companies]);

  const handleCreate = async () => {
    if (!form.announcement_id || !form.company_id) return;
    setCreating(true);
    setCreateError(null);
    try {
      const app = await createApplication({
        announcement_id: form.announcement_id,
        company_id: form.company_id,
        bid_price: form.bid_price ? Number(form.bid_price) : undefined,
        notes: form.notes || undefined,
      });
      setApps((p) => [app, ...p]);
      setShowForm(false);
      setForm({ announcement_id: 0, company_id: 0, bid_price: "", notes: "" });
      router.push(`/applications/${app.id}`);
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : "지원 생성 실패");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 검색 + 필터 바 */}
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="공고명, 발주처, 회사, 메모 검색..."
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div className="flex gap-1.5 flex-wrap">
          {FILTER_OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setStatusFilter(value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === value
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {label}
              {value === "" && apps.length > 0 && (
                <span className="ml-1 text-xs opacity-70">({apps.length})</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 결과 수 */}
      {(keyword || statusFilter) && (
        <p className="text-xs text-gray-400">
          {filtered.length}건 표시 중
          {(keyword || statusFilter) && (
            <button
              onClick={() => { setKeyword(""); setStatusFilter(""); }}
              className="ml-2 text-blue-500 hover:underline"
            >
              초기화
            </button>
          )}
        </p>
      )}

      {/* 지원 건 목록 */}
      {filtered.length === 0 && !showForm && (
        <div className="text-center py-10 text-gray-400 text-sm">
          {keyword || statusFilter ? "검색 결과 없음" : "입찰 지원 내역이 없습니다"}
        </div>
      )}

      {filtered.map((app) => {
        const ann = announcements.find((a) => a.id === app.announcement_id);
        const co = companies.find((c) => c.id === app.company_id);
        const st = STATUS_LABEL[app.status] ?? { label: app.status, cls: "bg-gray-100 text-gray-600" };
        const approved = app.documents.filter((d) => d.status === "approved").length;
        const total = app.documents.length;

        return (
          <a
            key={app.id}
            href={`/applications/${app.id}`}
            className="block bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-900 truncate">
                  {ann?.title ?? `공고 #${app.announcement_id}`}
                </div>
                <div className="text-sm text-gray-500 mt-0.5">
                  {co?.name ?? `회사 #${app.company_id}`} · {ann?.organization}
                </div>
              </div>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${st.cls}`}>
                {st.label}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
              {total > 0 && <span>서류 승인 {approved}/{total}</span>}
              {app.bid_price && <span>투찰가 {app.bid_price.toLocaleString()}원</span>}
              {app.notes && <span className="truncate max-w-[150px]">{app.notes}</span>}
              <span className="ml-auto text-xs text-gray-400">
                {new Date(app.created_at).toLocaleDateString("ko-KR")}
              </span>
            </div>
          </a>
        );
      })}

      {/* 신규 지원 폼 */}
      {showForm ? (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <h2 className="font-semibold text-gray-900">입찰 지원 시작</h2>
          <p className="text-sm text-gray-500">
            공고와 회사를 선택하면 필요 서류를 자동으로 식별하고 초안을 생성합니다.
          </p>

          <div>
            <label className="text-sm text-gray-600 mb-1 block">공고 선택 *</label>
            <select
              value={form.announcement_id}
              onChange={(e) => setForm((p) => ({ ...p, announcement_id: Number(e.target.value) }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>공고를 선택하세요</option>
              {announcements.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.title} ({a.organization})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-600 mb-1 block">회사 선택 *</label>
            {companies.length === 0 ? (
              <p className="text-sm text-red-500">
                먼저 <a href="/companies" className="underline">회사 정보</a>를 등록해주세요.
              </p>
            ) : (
              <select
                value={form.company_id}
                onChange={(e) => setForm((p) => ({ ...p, company_id: Number(e.target.value) }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={0}>회사를 선택하세요</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-gray-600 mb-1 block">투찰가 (원)</label>
              <input
                type="number"
                value={form.bid_price}
                onChange={(e) => setForm((p) => ({ ...p, bid_price: e.target.value }))}
                placeholder="미정"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">메모</label>
              <input
                value={form.notes}
                onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {createError && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
              {createError}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={!form.announcement_id || !form.company_id || creating}
              className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {creating ? "서류 생성 중..." : "지원 시작 및 서류 자동 생성"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              취소
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowForm(true)}
          className="w-full border-2 border-dashed border-gray-300 rounded-xl py-4 text-sm text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-colors"
        >
          + 새 입찰 지원 시작
        </button>
      )}
    </div>
  );
}
