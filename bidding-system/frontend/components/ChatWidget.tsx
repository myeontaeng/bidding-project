"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { sendChat, type CollectionItem } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  text: string;
  announcements?: CollectionItem[];
}

function fmtBudget(v: number | null) {
  if (!v) return null;
  if (v >= 1_0000_0000) return `${(v / 1_0000_0000).toFixed(1)}억`;
  if (v >= 1_0000) return `${(v / 1_0000).toFixed(0)}만`;
  return v.toLocaleString();
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "안녕하세요! 공고 검색을 도와드립니다.\n예) \"IT서비스 10억 이상 공고 찾아줘\"",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const res = await sendChat(msg);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.message, announcements: res.announcements },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "오류가 발생했습니다. 다시 시도해주세요." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-2">
      {open && (
        <div className="bg-white border border-gray-200 rounded-2xl shadow-2xl w-80 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-blue-600 text-white px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-base">🤖</span>
              <span className="text-sm font-semibold">입찰 AI 어시스턴트</span>
            </div>
            <button onClick={() => setOpen(false)} className="text-blue-200 hover:text-white text-lg leading-none">✕</button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3 max-h-80">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] space-y-2`}>
                  <div
                    className={`px-3 py-2 rounded-xl text-sm whitespace-pre-wrap leading-relaxed ${
                      m.role === "user"
                        ? "bg-blue-600 text-white rounded-br-sm"
                        : "bg-gray-100 text-gray-800 rounded-bl-sm"
                    }`}
                  >
                    {m.text}
                  </div>
                  {m.announcements && m.announcements.length > 0 && (
                    <div className="space-y-1.5">
                      {m.announcements.map((ann) => (
                        <Link
                          key={ann.id}
                          href={`/announcements/${ann.id}`}
                          className="block bg-white border border-gray-200 rounded-lg px-3 py-2 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                          onClick={() => setOpen(false)}
                        >
                          <p className="text-xs font-medium text-gray-800 leading-snug line-clamp-2">{ann.title}</p>
                          <div className="flex items-center justify-between mt-1">
                            <p className="text-xs text-gray-400 truncate">{ann.organization}</p>
                            <div className="flex items-center gap-1.5 shrink-0 ml-2">
                              {ann.budget && <span className="text-xs text-gray-500">{fmtBudget(ann.budget)}원</span>}
                              {ann.dday !== null && ann.dday >= 0 && (
                                <span className={`text-xs font-semibold ${ann.dday <= 3 ? "text-red-600" : ann.dday <= 7 ? "text-amber-600" : "text-blue-600"}`}>
                                  D-{ann.dday}
                                </span>
                              )}
                            </div>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-xl rounded-bl-sm px-3 py-2 text-sm text-gray-400">
                  검색 중...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-100 p-2 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              placeholder="공고 검색..."
              className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              전송
            </button>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center text-xl transition-all"
        aria-label="AI 어시스턴트 열기"
      >
        {open ? "✕" : "🤖"}
      </button>
    </div>
  );
}
