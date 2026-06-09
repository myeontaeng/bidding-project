import { getServerToken } from "@/lib/server-auth";
import { fetchUsers, fetchMe } from "@/lib/api";
import { redirect } from "next/navigation";
import SettingsClient from "./SettingsClient";

export default async function SettingsPage() {
  const token = await getServerToken();
  if (!token) redirect("/login");

  const me = await fetchMe(token).catch(() => null);
  if (!me || me.role !== "admin") redirect("/");

  const users = await fetchUsers(token).catch(() => []);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">설정</h1>
        <p className="text-sm text-gray-500 mt-1">시스템 설정 및 권한 관리</p>
      </div>
      <SettingsClient initialUsers={users} currentUserId={me.id} />
    </main>
  );
}
