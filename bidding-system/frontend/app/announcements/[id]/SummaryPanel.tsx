"use client";

import { useState } from "react";
import { summarizeAnnouncement } from "@/lib/api";

export default function SummaryPanel({
  annId,
  initialDescription,
}: {
  annId: number;
  initialDescription: string | null;
}) {
  const [description, setDescription] = useState(initialDescription);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const { description: text } = await summarizeAnnouncement(annId);
      setDescription(text);
    } catch {
      setError("로그인 후 요약을 생성할 수 있습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">공고 요약</h2>
        <button
          onClick={generate}
          disabled={loading}
          className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg disabled:opacity-50 transition-colors"
        >
          {loading ? "생성 중..." : description ? "다시 생성" : "요약 생성"}
        </button>
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      {description ? (
        <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
          {description}
        </div>
      ) : (
        <p className="text-sm text-gray-400">
          위 버튼을 눌러 AI 요약을 생성하세요.
        </p>
      )}
    </div>
  );
}
