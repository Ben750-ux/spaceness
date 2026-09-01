// Palette de couleurs Spaceness
// Bleu principal #009fe3, vert succès #10b981, ambre accent

export const Colors = {
  primary: '#009fe3',
  primaryDark: '#0b6fb8',
  primaryLight: '#e0f4ff',
  secondary: '#10b981',
  secondaryLight: '#d1fae5',
  accent: '#f59e0b',
  danger: '#ef4444',
  warning: '#eab308',
  purple: '#8b5cf6',

  background: '#f5f7fb',
  surface: '#ffffff',
  surfaceMuted: '#f0f3f9',

  text: '#0f172a',
  textSecondary: '#64748b',
  textLight: '#94a3b8',
  border: '#e2e8f0',

  dark: {
    background: '#0b1120',
    surface: '#111a2e',
    surfaceMuted: '#1b2740',
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    border: '#1e293b',
  },
} as const;

export const Radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 999,
} as const;

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;
