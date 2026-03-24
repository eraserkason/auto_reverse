import type { AuthSession, AuthenticatedUser } from '@/types/auth';
import { loginByApi } from '@/views/api';

const SESSION_STORAGE_KEY = 'auth-session';
const SESSION_FALLBACK_DURATION_MS = 120 * 60 * 1000;

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const segments = token.split('.');
  if (typeof window === 'undefined' || segments.length < 2) {
    return null;
  }

  try {
    const normalizedPayload = segments[1]
      .replace(/-/g, '+')
      .replace(/_/g, '/')
      .padEnd(Math.ceil(segments[1].length / 4) * 4, '=');
    return JSON.parse(window.atob(normalizedPayload)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function resolveSessionExpiresAt(token: string, now: number): string {
  const payload = decodeJwtPayload(token);
  const exp = Number(payload?.exp);

  if (Number.isFinite(exp) && exp > 0) {
    return new Date(exp * 1000).toISOString();
  }

  return new Date(now + SESSION_FALLBACK_DURATION_MS).toISOString();
}

function createSession(token: string, user: AuthenticatedUser): AuthSession {
  const now = Date.now();
  return {
    token,
    user,
    loginAt: new Date(now).toISOString(),
    expiresAt: resolveSessionExpiresAt(token, now),
  };
}

function isSessionValid(session: AuthSession): boolean {
  return Date.parse(session.expiresAt) > Date.now();
}

export function getAuthSession(): AuthSession | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as AuthSession;
    if (!parsed?.token || !parsed?.user?.id || !parsed?.expiresAt) {
      clearAuthSession();
      return null;
    }
    if (!isSessionValid(parsed)) {
      clearAuthSession();
      return null;
    }
    return parsed;
  } catch {
    clearAuthSession();
    return null;
  }
}

export function setAuthSession(token: string, user: AuthenticatedUser): AuthSession {
  const session = createSession(token, user);
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  }
  return session;
}

export function clearAuthSession(): void {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  }
}

export async function loginWithCredentials(username: string, password: string): Promise<AuthSession | null> {
  try {
    const payload = await loginByApi(username.trim(), password);
    const user: AuthenticatedUser = {
      id: payload.user.id,
      username: payload.user.username,
      displayName: payload.user.username,
      role: 'user',
      createdAt: payload.user.createdAt,
    };
    return setAuthSession(payload.accessToken, user);
  } catch {
    return null;
  }
}
