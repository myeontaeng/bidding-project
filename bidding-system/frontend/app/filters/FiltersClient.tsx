"use client";

import { useState } from "react";
import { FilterConfig, createFilter, deleteFilter } from "@/lib/api";

interface Props {
  initialFilters: FilterConfig[];
}

const EMPTY = {
  name: "",
  keywords: [] as string[],
  categories: [] as string[],
  regions: [] as string[],
  organizations: [] as string[],
  budget_min: null as number | null,
  budget_max: null as number | null,
  notify_email: "",
  notify_slack: false,
  reminder_days: [7, 3, 1],
  active: true,
};

function TagInput({
  value,
  onChange,
  placeholder,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder: string;
}) {
  const [input, setInput] = useState("");
  const add = () => {
    const v = input.trim();
    if (v && !value.includes(v)) onChange([...value, v]);
    setInput("");
  };
  return (
    <div className="flex flex-wrap gap-1 border border-gray-300 rounded-lg p-2 min-h-[42px]">
      {value.map((t) => (
        <span
          key={t}
          className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
        >
          {t}
          <button
            type="button"
            onClick={() => onChange(value.filter((x) => x !== t))}
            className="hover:text-red-500"
          >
            ×
          </button>
        </span>
      ))}
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
        placeholder={value.length === 0 ? placeholder : ""}
        className="text-sm outline-none flex-1 min-w-[100px]"
      />
    </div>
  );
}

export default function FiltersClient({ initialFilters }: Props) {
  const [filters, setFilters] = useState(initialFilters);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const handleCreate = async () => {
    setSaving(true);
    try {
      const created = await createFilter({
        ...form,
        notify_email: form.notify_email || null,
        keywords: form.keywords.length ? form.keywords : null,
        categories: form.categories.length ? form.categories : null,
        regions: form.regions.length ? form.regions : null,
        organizations: form.organizations.length ? form.organizations : null,
      });
      setFilters((prev) => [...prev, created]);
      setForm(EMPTY);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    await deleteFilter(id);
    setFilters((prev) => prev.filter((f) => f.id !== id));
  };

  return (
    <div className="space-y-6">
      {/* 필터 목록 */}
      {filters.length === 0 ? (
        <p className="text-gray-400 text-sm text-center py-8">
          등록된 필터가 없습니다.
        </p>
      ) : (
        <div className="space-y-3">
          {filters.map((f) => (
            <div
              key={f.id}
              className="bg-white rounded-xl border border-gray-200 p-4 flex items-start justify-between gap-4"
            >
              <div className="flex-1">
                <div className="font-medium text-gray-900">{f.name}</div>
                <div className="mt-1 text-sm text-gray-500 space-y-0.5">
                  {f.keywords && (
                    <div>키워드: {f.keywords.join(", ")}</div>
                  )}
                  {f.categories && (
                    <div>업종: {f.categories.join(", ")}</div>
                  )}
                  {f.regions && <div>지역: {f.regions.join(", ")}</div>}
                  {f.notify_email && <div>이메일: {f.notify_email}</div>}
                  {f.notify_slack && (
                    <div className="text-green-600">슬랙 알림 활성</div>
                  )}
                  <div>
                    리마인더: D-{f.reminder_days.join(", D-")}
                  </div>
                </div>
              </div>
              <button
                onClick={() => handleDelete(f.id)}
                className="text-red-500 hover:text-red-700 text-sm"
              >
                삭제
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 필터 생성 폼 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
        <h2 className="font-semibold text-gray-900">새 필터 추가</h2>

        <div>
          <label className="text-sm text-gray-600 mb-1 block">필터 이름 *</label>
          <input
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="예: IT서비스 서울"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-600 mb-1 block">
              키워드 (Enter로 추가)
            </label>
            <TagInput
              value={form.keywords}
              onChange={(v) => setForm((p) => ({ ...p, keywords: v }))}
              placeholder="소프트웨어, 시스템..."
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">업종</label>
            <TagInput
              value={form.categories}
              onChange={(v) => setForm((p) => ({ ...p, categories: v }))}
              placeholder="IT서비스, 건설..."
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">지역</label>
            <TagInput
              value={form.regions}
              onChange={(v) => setForm((p) => ({ ...p, regions: v }))}
              placeholder="서울, 경기..."
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">발주처</label>
            <TagInput
              value={form.organizations}
              onChange={(v) => setForm((p) => ({ ...p, organizations: v }))}
              placeholder="행정안전부..."
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-gray-600 mb-1 block">예산 최소</label>
            <input
              type="number"
              value={form.budget_min ?? ""}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  budget_min: e.target.value ? Number(e.target.value) : null,
                }))
              }
              placeholder="0"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">예산 최대</label>
            <input
              type="number"
              value={form.budget_max ?? ""}
              onChange={(e) =>
                setForm((p) => ({
                  ...p,
                  budget_max: e.target.value ? Number(e.target.value) : null,
                }))
              }
              placeholder="무제한"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="text-sm text-gray-600 mb-1 block">
            알림 이메일
          </label>
          <input
            type="email"
            value={form.notify_email}
            onChange={(e) =>
              setForm((p) => ({ ...p, notify_email: e.target.value }))
            }
            placeholder="example@company.com"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            id="slack"
            type="checkbox"
            checked={form.notify_slack}
            onChange={(e) =>
              setForm((p) => ({ ...p, notify_slack: e.target.checked }))
            }
            className="rounded"
          />
          <label htmlFor="slack" className="text-sm text-gray-600">
            슬랙 알림 활성화
          </label>
        </div>

        <button
          onClick={handleCreate}
          disabled={!form.name || saving}
          className="w-full bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? "저장 중..." : "필터 추가"}
        </button>
      </div>
    </div>
  );
}
