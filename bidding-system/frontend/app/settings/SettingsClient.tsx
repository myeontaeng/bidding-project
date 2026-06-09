"use client";

import { useState } from "react";
import { createUser, updateUser, deleteUser, type UserInfo } from "@/lib/api";

const ROLE_LABEL: Record<string, { text: string; cls: string }> = {
  admin: { text: "관리자", cls: "bg-blue-100 text-blue-700" },
  partner: { text: "협력사", cls: "bg-green-100 text-green-700" },
};

function RoleBadge({ role }: { role: string }) {
  const r = ROLE_LABEL[role] ?? { text: role, cls: "bg-gray-100 text-gray-600" };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${r.cls}`}>{r.text}</span>
  );
}

function fmtDate(s: string) {
  return new Date(s).toLocaleDateString("ko-KR");
}

export default function SettingsClient({
  initialUsers,
  currentUserId,
}: {
  initialUsers: UserInfo[];
  currentUserId: number;
}) {
  const [users, setUsers] = useState<UserInfo[]>(initialUsers);
  const [tab, setTab] = useState<"users">("users");

  // 생성 폼
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<"admin" | "partner">("partner");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // 편집
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editRole, setEditRole] = useState<"admin" | "partner">("partner");
  const [editPassword, setEditPassword] = useState("");
  const [saving, setSaving] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreating(true);
    try {
      const user = await createUser({ username: newUsername, password: newPassword, role: newRole });
      setUsers((prev) => [...prev, user]);
      setNewUsername("");
      setNewPassword("");
      setNewRole("partner");
    } catch (err) {
      setCreateError((err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (user: UserInfo) => {
    setEditingId(user.id);
    setEditRole(user.role as "admin" | "partner");
    setEditPassword("");
  };

  const handleSave = async (userId: number) => {
    setSaving(true);
    try {
      const body: { role?: string; password?: string } = { role: editRole };
      if (editPassword) body.password = editPassword;
      const updated = await updateUser(userId, body);
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      setEditingId(null);
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (userId: number, username: string) => {
    if (!confirm(`"${username}" 계정을 삭제하시겠습니까?`)) return;
    try {
      await deleteUser(userId);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err) {
      alert((err as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      {/* 탭 */}
      <div className="border-b border-gray-200">
        <div className="flex gap-0">
          <button
            onClick={() => setTab("users")}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === "users"
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            사용자 권한 관리
          </button>
        </div>
      </div>

      {tab === "users" && (
        <div className="space-y-6">
          {/* 사용자 목록 */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">사용자 목록 ({users.length}명)</h2>
            </div>
            <div className="divide-y divide-gray-50">
              {users.map((user) => (
                <div key={user.id} className="px-5 py-3.5">
                  {editingId === user.id ? (
                    /* 편집 모드 */
                    <div className="flex flex-col sm:flex-row gap-3">
                      <span className="text-sm font-medium text-gray-800 w-32 shrink-0 pt-1.5">
                        {user.username}
                      </span>
                      <div className="flex flex-wrap gap-2 flex-1 items-start">
                        <select
                          value={editRole}
                          onChange={(e) => setEditRole(e.target.value as "admin" | "partner")}
                          className="text-sm border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="admin">관리자</option>
                          <option value="partner">협력사</option>
                        </select>
                        <input
                          type="password"
                          value={editPassword}
                          onChange={(e) => setEditPassword(e.target.value)}
                          placeholder="새 비밀번호 (변경 시)"
                          className="text-sm border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 w-44"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleSave(user.id)}
                            disabled={saving}
                            className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                          >
                            {saving ? "저장 중..." : "저장"}
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50"
                          >
                            취소
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* 조회 모드 */
                    <div className="flex items-center gap-3">
                      <div className="flex-1 flex items-center gap-3 min-w-0">
                        <span className="text-sm font-medium text-gray-800 truncate">{user.username}</span>
                        <RoleBadge role={user.role} />
                        {user.id === currentUserId && (
                          <span className="text-xs text-gray-400">(나)</span>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 shrink-0">{fmtDate(user.created_at)}</span>
                      <div className="flex gap-1.5 shrink-0">
                        <button
                          onClick={() => startEdit(user)}
                          className="text-xs text-blue-600 hover:underline px-2 py-1 rounded hover:bg-blue-50"
                        >
                          편집
                        </button>
                        {user.id !== currentUserId && (
                          <button
                            onClick={() => handleDelete(user.id, user.username)}
                            className="text-xs text-red-500 hover:underline px-2 py-1 rounded hover:bg-red-50"
                          >
                            삭제
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {users.length === 0 && (
                <p className="px-5 py-4 text-sm text-gray-400">사용자 없음</p>
              )}
            </div>
          </div>

          {/* 사용자 추가 */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-4">새 사용자 추가</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">사용자명</label>
                  <input
                    type="text"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    required
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="username"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">비밀번호</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={4}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="4자 이상"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">권한</label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as "admin" | "partner")}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="partner">협력사</option>
                    <option value="admin">관리자</option>
                  </select>
                </div>
              </div>

              {/* 권한 설명 */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className={`rounded-lg p-3 border ${newRole === "admin" ? "border-blue-200 bg-blue-50" : "border-gray-100 bg-gray-50"}`}>
                  <p className="font-semibold text-blue-700 mb-1">관리자</p>
                  <ul className="text-gray-600 space-y-0.5">
                    <li>• 모든 기능 접근</li>
                    <li>• 사용자 권한 관리</li>
                    <li>• 회사 정보 관리</li>
                    <li>• 알림 필터 설정</li>
                    <li>• 대시보드 전체 분석</li>
                  </ul>
                </div>
                <div className={`rounded-lg p-3 border ${newRole === "partner" ? "border-green-200 bg-green-50" : "border-gray-100 bg-gray-50"}`}>
                  <p className="font-semibold text-green-700 mb-1">협력사</p>
                  <ul className="text-gray-600 space-y-0.5">
                    <li>• 공고 조회 및 검색</li>
                    <li>• 입찰 지원 신청</li>
                    <li>• 가격 분석</li>
                    <li>• 북마크</li>
                    <li className="text-gray-400">• 설정/회사정보/필터 접근 불가</li>
                  </ul>
                </div>
              </div>

              {createError && <p className="text-sm text-red-500">{createError}</p>}
              <button
                type="submit"
                disabled={creating || !newUsername || !newPassword}
                className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {creating ? "추가 중..." : "+ 사용자 추가"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
