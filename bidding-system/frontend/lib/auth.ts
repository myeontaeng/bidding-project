export const TOKEN_KEY = 'auth_token';
export const ROLE_KEY = 'auth_role';

export function storeToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
  document.cookie = `${TOKEN_KEY}=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}

export function storeRole(role: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ROLE_KEY, role);
}

export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0`;
}

export function getClientToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getClientRole(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ROLE_KEY);
}

export function isAdmin(): boolean {
  return getClientRole() === 'admin';
}
