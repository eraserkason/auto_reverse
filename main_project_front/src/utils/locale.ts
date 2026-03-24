import { DEFAULT_LOCALE, SUPPORTED_LOCALES, type AppLocale } from '@/locales/types';

const LOCALE_STORAGE_KEY = 'app-locale';

export function isAppLocale(value: unknown): value is AppLocale {
  return typeof value === 'string' && SUPPORTED_LOCALES.includes(value as AppLocale);
}

export function getStoredLocale(): AppLocale {
  if (typeof window === 'undefined') {
    return DEFAULT_LOCALE;
  }

  const raw = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  if (!isAppLocale(raw)) {
    if (raw) {
      window.localStorage.removeItem(LOCALE_STORAGE_KEY);
    }
    return DEFAULT_LOCALE;
  }

  return raw;
}

export function setStoredLocale(locale: AppLocale): void {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
}
