import { computed, ref } from 'vue';

import type { AuthenticatedUser } from '@/types/auth';
import { clearAuthSession, getAuthSession, loginWithCredentials } from '@/utils/auth';

const currentUser = ref<AuthenticatedUser | null>(null);
let storageSyncBound = false;

function syncAuthState(): AuthenticatedUser | null {
  currentUser.value = getAuthSession()?.user ?? null;
  return currentUser.value;
}

function bindStorageSync(): void {
  if (storageSyncBound || typeof window === 'undefined') {
    return;
  }
  window.addEventListener('storage', () => {
    syncAuthState();
  });
  storageSyncBound = true;
}

syncAuthState();

export function useAuth() {
  syncAuthState();
  bindStorageSync();

  const isAuthenticated = computed(() => currentUser.value !== null);

  async function login(username: string, password: string): Promise<boolean> {
    const session = await loginWithCredentials(username, password);
    if (!session) {
      return false;
    }
    currentUser.value = session.user;
    return true;
  }

  function logout(): void {
    clearAuthSession();
    syncAuthState();
  }

  return {
    isAuthenticated,
    currentUser,
    login,
    logout,
  };
}
