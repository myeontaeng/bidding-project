import { NextRequest, NextResponse } from "next/server";

const PROTECTED = ["/filters", "/companies", "/applications", "/dashboard"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED.some((p) => pathname.startsWith(p));

  if (isProtected) {
    const token = request.cookies.get("auth_token")?.value;
    if (!token) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/filters", "/companies", "/applications/:path*", "/dashboard"],
};
