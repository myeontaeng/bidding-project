"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getClientToken, removeToken } from "@/lib/auth";
import { getBookmarkCount } from "@/lib/bookmarks";

const NAV = [
  { href: "/", label: "공고" },
  { href: "/bookmarks", label: "북마크" },
  { href: "/applications", label: "입찰 지원", auth: true },
  { href: "/companies", label: "회사 정보", auth: true },
  { href: "/price", label: "가격 분석" },
  { href: "/dashboard", label: "대시보드", auth: true },
  { href: "/filters", label: "알림 필터", auth: true },
];

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [bmCount, setBmCount] = useState(0);

  useEffect(() => {
    setIsLoggedIn(!!getClientToken());
  }, [pathname]);

  useEffect(() => {
    const update = () => setBmCount(getBookmarkCount());
    update();
    window.addEventListener("bookmarks-changed", update);
    return () => window.removeEventListener("bookmarks-changed", update);
  }, []);

  const handleLogout = () => {
    removeToken();
    setIsLoggedIn(false);
    router.push("/");
    router.refresh();
  };

  if (pathname === "/login") return null;

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-1 overflow-x-auto">
          {NAV.map(({ href, label, auth }) => {
            if (auth && !isLoggedIn) return null;
            const active = pathname === href || (href !== "/" && pathname.startsWith(href));
            return (
              <a
                key={href}
                href={href}
                className={`px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors flex items-center gap-1 ${
                  active
                    ? "bg-blue-50 text-blue-700 font-medium"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                }`}
              >
                {label}
                {href === "/bookmarks" && bmCount > 0 && (
                  <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-1.5 py-0.5 rounded-full leading-none">
                    {bmCount}
                  </span>
                )}
              </a>
            );
          })}
        </div>
        <div className="ml-4 flex-shrink-0">
          {isLoggedIn ? (
            <button
              onClick={handleLogout}
              className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
            >
              로그아웃
            </button>
          ) : (
            <a
              href="/login"
              className="text-xs text-blue-600 hover:underline px-2 py-1"
            >
              로그인
            </a>
          )}
        </div>
      </div>
    </nav>
  );
}
