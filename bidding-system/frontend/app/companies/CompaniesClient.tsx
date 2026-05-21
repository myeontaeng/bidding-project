"use client";

import { useState } from "react";
import { Company, createCompany } from "@/lib/api";

const EMPTY = {
  name: "", business_number: "", ceo_name: "", address: "",
  phone: "", email: "", bank_account: "", cert_serial: "", business_types: "",
};

export default function CompaniesClient({ initialCompanies }: { initialCompanies: Company[] }) {
  const [companies, setCompanies] = useState(initialCompanies);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const f = (k: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleCreate = async () => {
    if (!form.name || !form.business_number) return;
    setSaving(true);
    try {
      const created = await createCompany(form as never);
      setCompanies((p) => [...p, created]);
      setForm(EMPTY);
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {companies.length === 0 && !showForm && (
        <p className="text-gray-400 text-sm text-center py-8">등록된 회사가 없습니다.</p>
      )}

      {companies.map((c) => (
        <div key={c.id} className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="font-semibold text-gray-900">{c.name}</div>
              <div className="text-sm text-gray-500 mt-1 space-y-0.5">
                <div>사업자번호: {c.business_number}</div>
                {c.ceo_name && <div>대표자: {c.ceo_name}</div>}
                {c.email && <div>이메일: {c.email}</div>}
                {c.business_types && <div>업종: {c.business_types}</div>}
              </div>
            </div>
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">활성</span>
          </div>
        </div>
      ))}

      {showForm ? (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
          <h2 className="font-semibold text-gray-900">회사 정보 등록</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { k: "name", label: "회사명 *", type: "text" },
              { k: "business_number", label: "사업자등록번호 *", type: "text" },
              { k: "ceo_name", label: "대표자명", type: "text" },
              { k: "phone", label: "전화번호", type: "text" },
              { k: "email", label: "이메일", type: "email" },
              { k: "business_types", label: "업종 (쉼표 구분)", type: "text" },
            ].map(({ k, label, type }) => (
              <div key={k}>
                <label className="text-sm text-gray-600 mb-1 block">{label}</label>
                <input
                  type={type}
                  value={form[k as keyof typeof EMPTY]}
                  onChange={f(k as keyof typeof EMPTY)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">주소</label>
            <input
              value={form.address}
              onChange={f("address")}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <p className="text-xs text-gray-400">
            🔒 사업자번호·계좌·인증서 정보는 AES-128 암호화 저장됩니다.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={!form.name || !form.business_number || saving}
              className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "저장 중..." : "등록"}
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
          + 회사 정보 추가
        </button>
      )}
    </div>
  );
}
