/** Presentation helpers for money / percentages. No Intl dependency (Hermes-safe). */

const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  INR: '₹',
  JPY: '¥',
};

/** Group a plain numeric string (optionally signed / with a fraction) with commas. */
function group(numStr: string): string {
  const negative = numStr.startsWith('-');
  const abs = negative ? numStr.slice(1) : numStr;
  const dot = abs.indexOf('.');
  const intPart = dot === -1 ? abs : abs.slice(0, dot);
  const fracPart = dot === -1 ? '' : abs.slice(dot + 1);
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return `${negative ? '-' : ''}${grouped}${fracPart ? `.${fracPart}` : ''}`;
}

export function formatCurrency(value: number, currency = 'USD'): string {
  const safe = Number.isFinite(value) ? value : 0;
  const symbol = CURRENCY_SYMBOLS[currency] ?? `${currency} `;
  const body = group(Math.abs(safe).toFixed(2));
  return `${safe < 0 ? '-' : ''}${symbol}${body}`;
}

export function formatPercent(value: number): string {
  const safe = Number.isFinite(value) ? value : 0;
  const sign = safe >= 0 ? '+' : '';
  return `${sign}${safe.toFixed(2)}%`;
}

export function formatNumber(value: number, maxDecimals = 4): string {
  const safe = Number.isFinite(value) ? value : 0;
  let s = safe.toFixed(maxDecimals);
  if (s.includes('.')) {
    s = s.replace(/0+$/, '').replace(/\.$/, '');
  }
  return group(s);
}

/** Tailwind text color class for a signed value (gain/loss). */
export function pnlColor(value: number): string {
  return value >= 0 ? 'text-emerald-600' : 'text-rose-600';
}
