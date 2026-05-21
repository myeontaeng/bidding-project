"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BidApplication, BidDocument, reviewDocument, submitApplication, updateApplicationResult } from "@/lib/api";

const DOC_LABELS: Record<string, string> = {
  bid_application: "입찰참가신청서",
  proposal: "제안서",
  price_breakdown: "가격산출내역서",
  company_profile: "회사소개서",
  cert_capability: "역량확인서",
};

const STATUS_STYLE: Record<string, string> = {
  draft:     "bg-gray-100 text-gray-600",
  review:    "bg-yellow-100 text-yellow-700",
  approved:  "bg-green-100 text-green-700",
  rejected:  "bg-red-100 text-red-600",
  submitted: "bg-blue-100 text-blue-700",
};

const STATUS_KR: Record<string, string> = {
  draft: "초안", review: "검토중", approved: "승인", rejected: "반려", submitted: "제출완료",
};

function DocumentReviewer({
  doc,
  onUpdated,
}: {
  doc: BidDocument;
  onUpdated: (updated: Partial<BidDocument> & { id: number }) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  const act = async (action: "approve" | "reject") => {
    setLoading(true);
    try {
      const updated = await reviewDocument(doc.id, action, note || undefined);
      onUpdated(updated);
      setNote("");
    } finally {
      setLoading(false);
    }
  };

  const canReview = doc.status === "draft" || doc.status === "review";

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 text-left"
      >
        <div className="flex items-center gap-3">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_STYLE[doc.status] ?? ""}`}>
            {STATUS_KR[doc.status] ?? doc.status}
          </span>
          <span className="font-medium text-gray-900">
            {DOC_LABELS[doc.doc_type] ?? doc.doc_type}
          </span>
        </div>
        <span className="text-gray-400 text-sm">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 p-4 space-y-4">
          <pre className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap font-sans max-h-96 overflow-y-auto">
            {doc.content}
          </pre>

          {doc.reviewer_note && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800">
              검토 의견: {doc.reviewer_note}
            </div>
          )}

          {canReview && (
            <div className="space-y-2">
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="검토 의견 (선택)"
                rows={2}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => act("approve")}
                  disabled={loading}
                  className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                >
                  승인
                </button>
                <button
                  onClick={() => act("reject")}
                  disabled={loading}
                  className="flex-1 bg-red-500 text-white py-2 rounded-lg text-sm font-medium hover:bg-red-600 disabled:opacity-50"
                >
                  반려
                </button>
              </div>
            </div>
          )}

          {doc.approved_at && (
            <p className="text-xs text-gray-400">
              승인: {new Date(doc.approved_at).toLocaleString("ko-KR")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

const RESULT_KR: Record<string, string> = { won: "낙찰", lost: "유찰", pending: "진행중" };
const RESULT_STYLE: Record<string, string> = {
  won: "bg-green-100 text-green-700",
  lost: "bg-red-100 text-red-600",
  pending: "bg-gray-100 text-gray-600",
};

function ResultInputPanel({ appId, initialResult }: { appId: number; initialResult: string | null }) {
  const [result, setResult] = useState<"won" | "lost">("won");
  const [resultPrice, setResultPrice] = useState("");
  const [winnerPrice, setWinnerPrice] = useState("");
  const [ourRank, setOurRank] = useState("");
  const [totalBidders, setTotalBidders] = useState("");
  const [saved, setSaved] = useState(initialResult);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    setLoading(true);
    try {
      await updateApplicationResult(appId, {
        result,
        result_price: resultPrice ? parseFloat(resultPrice) : undefined,
        winner_price: winnerPrice ? parseFloat(winnerPrice) : undefined,
        our_rank: ourRank ? parseInt(ourRank) : undefined,
        total_bidders: totalBidders ? parseInt(totalBidders) : undefined,
      });
      setSaved(result);
    } catch {
      alert("결과 저장 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-700">입찰 결과 입력</span>
        {saved && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${RESULT_STYLE[saved] ?? ""}`}>
            {RESULT_KR[saved] ?? saved}
          </span>
        )}
      </div>

      <div className="flex gap-2">
        {(["won", "lost"] as const).map((r) => (
          <button
            key={r}
            onClick={() => setResult(r)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
              result === r
                ? r === "won" ? "bg-green-600 text-white border-green-600" : "bg-red-500 text-white border-red-500"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
            }`}
          >
            {r === "won" ? "낙찰" : "유찰"}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">낙찰가 (원)</label>
          <input
            type="number"
            value={result === "won" ? resultPrice : winnerPrice}
            onChange={(e) => result === "won" ? setResultPrice(e.target.value) : setWinnerPrice(e.target.value)}
            placeholder="0"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">순위</label>
          <input
            type="number"
            value={ourRank}
            onChange={(e) => setOurRank(e.target.value)}
            placeholder="예: 2"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">총 투찰 업체 수</label>
          <input
            type="number"
            value={totalBidders}
            onChange={(e) => setTotalBidders(e.target.value)}
            placeholder="예: 8"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {result === "lost" && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">1위 낙찰가 (원)</label>
            <input
              type="number"
              value={winnerPrice}
              onChange={(e) => setWinnerPrice(e.target.value)}
              placeholder="0"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}
      </div>

      <button
        onClick={handleSave}
        disabled={loading}
        className="w-full bg-blue-700 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
      >
        {loading ? "저장 중..." : "결과 저장"}
      </button>
    </div>
  );
}

export default function ApplicationDetailClient({ app }: { app: BidApplication }) {
  const router = useRouter();
  const [docs, setDocs] = useState(app.documents);
  const [status, setStatus] = useState(app.status);
  const [submitting, setSubmitting] = useState(false);

  const updateDoc = (updated: Partial<BidDocument> & { id: number }) => {
    setDocs((prev) => prev.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)));
  };

  const allApproved = docs.length > 0 && docs.every((d) => d.status === "approved");

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const result = await submitApplication(app.id);
      setStatus(result.status);
      setDocs((prev) => prev.map((d) => ({ ...d, status: "submitted" })));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "제출 실패";
      alert(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const approved = docs.filter((d) => d.status === "approved").length;

  return (
    <div className="space-y-4">
      {/* 진행 현황 */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-700">서류 승인 현황</span>
          <span className="text-sm text-gray-500">{approved}/{docs.length} 승인</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all"
            style={{ width: `${docs.length ? (approved / docs.length) * 100 : 0}%` }}
          />
        </div>
      </div>

      {/* 서류 목록 */}
      <div className="space-y-2">
        {docs.map((doc) => (
          <DocumentReviewer key={doc.id} doc={doc} onUpdated={updateDoc} />
        ))}
      </div>

      {/* 제출 버튼 - HITL */}
      {status !== "submitted" && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-3">
          <div>
            <p className="text-sm font-medium text-amber-800">전자입찰 제출</p>
            <p className="text-xs text-amber-700 mt-0.5">
              모든 서류 승인 후 제출 가능합니다. 공동인증서 처리는 담당자가 직접 진행해야 합니다.
            </p>
          </div>
          <button
            onClick={handleSubmit}
            disabled={!allApproved || submitting}
            className="w-full bg-amber-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting
              ? "제출 중..."
              : allApproved
              ? "나라장터 전자입찰 제출 (담당자 인증서 확인 필요)"
              : `미승인 서류 ${docs.length - approved}건 남음`}
          </button>
        </div>
      )}

      {status === "submitted" && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
          <p className="font-medium text-green-800">제출 완료</p>
          <p className="text-sm text-green-600 mt-0.5">나라장터에서 접수 확인 후 상태가 업데이트됩니다.</p>
        </div>
      )}

      {/* 결과 입력 - 제출 완료 건만 */}
      {(status === "submitted" || status === "won" || status === "lost") && (
        <ResultInputPanel
          appId={app.id}
          initialResult={((app as unknown) as Record<string, unknown>).result as string | null ?? null}
        />
      )}
    </div>
  );
}
