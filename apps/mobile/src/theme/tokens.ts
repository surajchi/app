/** Design tokens shared across the app (mirrors tailwind.config brand colors). */
export const colors = {
  brand: '#4f46e5',
  brandDark: '#4338ca',
  text: '#0f172a',
  textMuted: '#64748b',
  border: '#cbd5e1',
  danger: '#ef4444',
  surface: '#ffffff',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;
