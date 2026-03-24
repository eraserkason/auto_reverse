import { computed, ref } from 'vue';

import { LOCALE_NATIVE_LABELS, messages, type MessageTree } from '@/locales/messages';
import { DEFAULT_LOCALE, type AppLocale } from '@/locales/types';
import { getStoredLocale, setStoredLocale } from '@/utils/locale';

type TranslateParams = Record<string, unknown>;

const currentLocale = ref<AppLocale>(DEFAULT_LOCALE);

function resolveMessage(tree: MessageTree, key: string): string | undefined {
  const result = key.split('.').reduce<unknown>((current, segment) => {
    if (!current || typeof current !== 'object') {
      return undefined;
    }
    return (current as Record<string, unknown>)[segment];
  }, tree);

  return typeof result === 'string' ? result : undefined;
}

function interpolate(message: string, params?: TranslateParams): string {
  if (!params) {
    return message;
  }

  return message.replace(/\{(\w+)\}/g, (_, token: string) => String(params[token] ?? `{${token}}`));
}

function classifyStatus(status: string): 'completed' | 'running' | 'queued' | 'pending' | 'error' | 'skipped' | 'unknown' {
  const normalized = status.trim().toLowerCase();

  if (!normalized) {
    return 'unknown';
  }
  if (normalized.includes('success') || normalized.includes('done') || normalized.includes('complete')) {
    return 'completed';
  }
  if (normalized.includes('running') || normalized.includes('process')) {
    return 'running';
  }
  if (normalized.includes('queue')) {
    return 'queued';
  }
  if (normalized.includes('pending')) {
    return 'pending';
  }
  if (normalized.includes('skip')) {
    return 'skipped';
  }
  if (normalized.includes('fail') || normalized.includes('error')) {
    return 'error';
  }
  return 'unknown';
}

function normalizeDateInput(value?: string | number | Date | null): Date | null {
  if (value === undefined || value === null || value === '') {
    return null;
  }

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function initializeLocale(): void {
  currentLocale.value = getStoredLocale();
}

initializeLocale();

export function useLocale() {
  const locale = computed(() => currentLocale.value);

  const localeOptions = computed(() => [
    { value: 'zh-CN' as const, ...LOCALE_NATIVE_LABELS['zh-CN'] },
    { value: 'en-US' as const, ...LOCALE_NATIVE_LABELS['en-US'] },
  ]);

  function setLocale(next: AppLocale): void {
    currentLocale.value = next;
    setStoredLocale(next);
  }

  function t(key: string, params?: TranslateParams): string {
    const localized = resolveMessage(messages[currentLocale.value], key) ?? resolveMessage(messages[DEFAULT_LOCALE], key) ?? key;
    return interpolate(localized, params);
  }

  function formatDateTime(
    value?: string | number | Date | null,
    options?: Intl.DateTimeFormatOptions,
  ): string {
    const date = normalizeDateInput(value);
    if (!date) {
      return t('common.misc.empty');
    }

    return new Intl.DateTimeFormat(currentLocale.value, options).format(date);
  }

  function formatTime(value?: string | number | Date | null): string {
    return formatDateTime(value, {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function getTaskStatusLabel(status: string): string {
    const type = classifyStatus(status);
    return t(`common.status.${type}`);
  }

  function getResultStatusLabel(success: boolean): string {
    return success ? t('common.status.success') : t('common.status.failed');
  }

  function getHealthStatusLabel(status: string): string {
    const normalized = status.trim().toLowerCase();

    if (!normalized) {
      return t('common.status.pendingSync');
    }
    if (normalized.includes('ok') || normalized.includes('up') || normalized.includes('healthy')) {
      return t('common.status.normal');
    }
    if (normalized.includes('warn')) {
      return t('common.status.warning');
    }
    if (normalized.includes('error') || normalized.includes('down') || normalized.includes('fail')) {
      return t('common.status.error');
    }
    return t('common.status.pendingSync');
  }

  return {
    locale,
    localeOptions,
    setLocale,
    t,
    formatDateTime,
    formatTime,
    getTaskStatusLabel,
    getResultStatusLabel,
    getHealthStatusLabel,
  };
}
