"use client";

import { useState } from "react";
import { Company, CertificationInfo, ExpiringCert, createCompany, fetchExpiringCerts } from "@/lib/api";

const EMPTY = {
  name: "", business_number: "", ceo_name: "", address: "",
  phone: "", email: "", bank_account: "", cert_serial: "", business_types: "",
};

function ExpiryWarning({ certs }: { certs: ExpiringCert[] }) {
  if (certs.length === 0) return null;
  const urgent = certs.filter((c) => c.days_remaining <= 30);
  const soon = certs.filter((c) => c.days_remaining > 30 && c.days_remaining <= 90);
  return (
    <div className="space-y-2">
      {certs.filter((c) => c.expired).length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3">
          <p className="text-sm font-semibold text-red-700 mb-1">만료된 인증서</p>
          {certs.filter((c) => c.expired).map((c) => (
            <p key={c.cert_name + c.company_id} className="text-xs text-red-600">
              {c.company_name} — {c.cert_name} ({c.expiry_date} 만료)
            </p>
          ))}
        </div>
      )}
      {urgent.filter((c) => !c.expired).length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-3">
          <p className="text-sm font-semibold text-orange-700 mb-1">30일 이내 만료</p>
          {urgent.filter((c) => !c.expired).map((c) => (
            <p key={c.cert_name + c.company_id} className="text-xs text-orange-600">
              {c.company_name} — {c.cert_name} (D-{c.days_remaining}, {c.expiry_date})
            </p>
          ))}
        </div>
      )}
      {soon.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3">
          <p className="text-sm font-semibold text-yellow-700 mb-1">90일 이내 만료</p>
          {soon.map((c) => (
            <p key={c.cert_name + c.company_id} className="text-xs text-yellow-600">
              {c.company_name} — {c.cert_name} (D-{c.days_remaining}, {c.expiry_date})
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

const EMPTY_CERT: CertificationInfo = { name: "", expiry_date: "", cert_type: "" };

export default function CompaniesClient({ initialCompanies, expiringCerts }: {
  initialCompanies: Company[];
  expiringCerts: ExpiringCert[];
}) {
  const [companies, setCompanies] = useState(initialCompanies);
  const [form, setForm] = useState(EMPTY);
  const [certs, setCerts] = useState<CertificationInfo[]>([]);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const f = (k: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleCreate = async () => {
    if (!form.name || !form.business_number) return;
    setSaving(true);
    try {
      const payload = {
        ...form,
        certifications: certs.filter((c) => c.name && c.expiry_date),
      };
      const created = await createCompany(payload as never);
      setCompanies((p) => [...p, created]);
      setForm(EMPTY);
      setCerts([]);
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <ExpiryWarning certs={expiringCerts} />

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
          {/* 인증서 만료일 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-gray-600">인증서 / 면허 만료일</label>
              <button
                type="button"
                onClick={() => setCerts((p) => [...p, { ...EMPTY_CERT }])}
                className="text-xs text-blue-600 hover:underline"
              >
                + 추가
              </button>
            </div>
            {certs.map((cert, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input
                  placeholder="인증서명 (예: 건설업 면허)"
                  value={cert.name}
                  onChange={(e) => setCerts((p) => p.map((c, j) => j === i ? { ...c, name: e.target.value } : c))}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="date"
                  value={cert.expiry_date}
                  onChange={(e) => setCerts((p) => p.map((c, j) => j === i ? { ...c, expiry_date: e.target.value } : c))}
                  className="border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={() => setCerts((p) => p.filter((_, j) => j !== i))}
                  className="text-gray-400 hover:text-red-500 px-1"
                >
                  ✕
                </button>
              </div>
            ))}
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
