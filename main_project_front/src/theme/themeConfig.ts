import type { GlobalThemeOverrides } from 'naive-ui';

export const lightThemeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#2563eb',
    primaryColorHover: '#3b82f6',
    primaryColorPressed: '#1d4ed8',
    primaryColorSuppl: '#2563eb',
    infoColor: '#0284c7',
    successColor: '#059669',
    warningColor: '#d97706',
    errorColor: '#dc2626',

    borderRadius: '16px',
    borderRadiusSmall: '12px',
    fontFamily:
      '"Fira Sans", "IBM Plex Sans", "Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
    fontFamilyMono:
      '"Fira Code", "JetBrains Mono", "IBM Plex Mono", "SFMono-Regular", Consolas, monospace',

    bodyColor: '#f4f7fb',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
    tableColor: '#ffffff',
    tableColorHover: '#f8fbff',
    tableHeaderColor: '#eef3fb',
    inputColorDisabled: '#edf2f8',

    textColorBase: '#111827',
    textColor1: '#0f172a',
    textColor2: '#334155',
    textColor3: '#64748b',
    placeholderColor: '#94a3b8',
    placeholderColorDisabled: '#a8b4c3',
    iconColor: '#475569',
    iconColorHover: '#1e293b',
    iconColorPressed: '#0f172a',

    borderColor: '#d9e2ef',
    dividerColor: '#e8eef7',

    closeIconColor: '#475569',
    closeIconColorHover: '#1e293b',
    closeIconColorPressed: '#0f172a',
    closeColorHover: 'rgba(148, 163, 184, 0.12)',
    closeColorPressed: 'rgba(148, 163, 184, 0.2)',

    boxShadow1: '0 1px 2px rgba(15, 23, 42, 0.05)',
    boxShadow2: '0 10px 24px rgba(15, 23, 42, 0.08)',
    boxShadow3: '0 18px 40px rgba(15, 23, 42, 0.12)',
  },
  Layout: {
    color: 'transparent',
    siderColor: '#f8fbff',
    headerColor: 'rgba(244, 247, 251, 0.82)',
    footerColor: '#f4f7fb',
  },
  Card: {
    borderRadius: '18px',
    color: '#ffffff',
    colorEmbedded: '#f6f9fc',
    borderColor: '#dbe4f0',
    titleTextColor: '#0f172a',
    textColor: '#334155',
    actionColor: '#f8fbff',
  },
  DataTable: {
    thColor: '#eef3fb',
    tdColor: '#ffffff',
    tdColorHover: '#f8fbff',
    borderColor: '#dbe4f0',
    thFontWeight: '700',
  },
  Input: {
    color: '#ffffff',
    colorFocus: '#ffffff',
    colorDisabled: '#edf2f8',
    textColor: '#0f172a',
    placeholderColor: '#94a3b8',
    border: '1px solid #d7e0ec',
    borderHover: '1px solid #93c5fd',
    borderFocus: '1px solid #60a5fa',
    boxShadowFocus: '0 0 0 3px rgba(37, 99, 235, 0.12)',
    caretColor: '#2563eb',
  },
  Select: {
    peers: {
      InternalSelection: {
        color: '#ffffff',
        textColor: '#0f172a',
        placeholderColor: '#94a3b8',
      },
    },
  },
  Tabs: {
    tabBorderRadius: '12px',
    tabColorSegment: '#e8eef7',
    tabTextColorSegment: '#64748b',
    tabTextColorActiveSegment: '#0f172a',
    tabColorActiveSegment: '#ffffff',
    panePaddingMedium: '16px 0 0',
  },
  Tag: {
    borderRadius: '999px',
    fontWeight: '600',
  },
  Button: {
    borderRadiusTiny: '12px',
    borderRadiusSmall: '12px',
    borderRadiusMedium: '14px',
    borderRadiusLarge: '16px',
    fontWeight: '600',
    textColorPrimary: '#ffffff',
  },
  PageHeader: {
    titleFontWeight: '800',
    backSize: '18px',
  },
};

export const darkThemeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#7aa2ff',
    primaryColorHover: '#95b7ff',
    primaryColorPressed: '#5f89ee',
    primaryColorSuppl: '#7aa2ff',
    infoColor: '#38bdf8',
    successColor: '#22c55e',
    warningColor: '#f59e0b',
    errorColor: '#f87171',

    borderRadius: '16px',
    borderRadiusSmall: '12px',
    fontFamily:
      '"Fira Sans", "IBM Plex Sans", "Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
    fontFamilyMono:
      '"Fira Code", "JetBrains Mono", "IBM Plex Mono", "SFMono-Regular", Consolas, monospace',

    bodyColor: '#0b1220',
    cardColor: '#101a2c',
    modalColor: '#101a2c',
    popoverColor: '#101a2c',
    tableColor: '#101a2c',
    tableColorHover: '#162238',
    tableHeaderColor: '#0d1728',
    inputColorDisabled: '#0b1423',

    textColorBase: '#edf3ff',
    textColor1: '#f8fbff',
    textColor2: '#c7d4e6',
    textColor3: '#8da0b8',
    placeholderColor: '#6b8099',
    placeholderColorDisabled: '#51647c',
    iconColor: '#c7d4e6',
    iconColorHover: '#edf3ff',
    iconColorPressed: '#f8fbff',

    borderColor: 'rgba(143, 163, 191, 0.18)',
    dividerColor: 'rgba(143, 163, 191, 0.12)',

    closeIconColor: '#c7d4e6',
    closeIconColorHover: '#edf3ff',
    closeIconColorPressed: '#f8fbff',
    closeColorHover: 'rgba(255, 255, 255, 0.08)',
    closeColorPressed: 'rgba(255, 255, 255, 0.12)',

    boxShadow1: '0 6px 12px rgba(2, 6, 23, 0.16)',
    boxShadow2: '0 14px 30px rgba(2, 6, 23, 0.24)',
    boxShadow3: '0 24px 48px rgba(2, 6, 23, 0.32)',
  },
  Layout: {
    color: 'transparent',
    siderColor: '#0d1728',
    headerColor: 'rgba(11, 18, 32, 0.82)',
    footerColor: '#0b1220',
  },
  Card: {
    borderRadius: '18px',
    color: '#101a2c',
    colorEmbedded: '#0c1625',
    borderColor: 'rgba(143, 163, 191, 0.16)',
    titleTextColor: '#f8fbff',
    textColor: '#c7d4e6',
    actionColor: 'rgba(255, 255, 255, 0.06)',
  },
  DataTable: {
    thColor: '#0d1728',
    tdColor: '#101a2c',
    tdColorHover: '#162238',
    borderColor: 'rgba(143, 163, 191, 0.14)',
    thFontWeight: '700',
  },
  Input: {
    color: '#0c1625',
    colorFocus: '#101e34',
    colorDisabled: '#09111e',
    textColor: '#edf3ff',
    placeholderColor: '#6b8099',
    border: '1px solid rgba(143, 163, 191, 0.18)',
    borderHover: '1px solid rgba(122, 162, 255, 0.36)',
    borderFocus: '1px solid rgba(122, 162, 255, 0.52)',
    boxShadowFocus: '0 0 0 3px rgba(122, 162, 255, 0.12)',
    caretColor: '#95b7ff',
  },
  Select: {
    peers: {
      InternalSelection: {
        color: '#0c1625',
        textColor: '#edf3ff',
        placeholderColor: '#6b8099',
      },
    },
  },
  Tabs: {
    tabBorderRadius: '12px',
    tabColorSegment: '#0d1728',
    tabTextColorSegment: '#8da0b8',
    tabTextColorActiveSegment: '#f8fbff',
    tabColorActiveSegment: '#162238',
    panePaddingMedium: '16px 0 0',
  },
  Tag: {
    borderRadius: '999px',
    fontWeight: '600',
  },
  Button: {
    borderRadiusTiny: '12px',
    borderRadiusSmall: '12px',
    borderRadiusMedium: '14px',
    borderRadiusLarge: '16px',
    fontWeight: '600',
  },
  PageHeader: {
    titleFontWeight: '800',
    backSize: '18px',
  },
};
