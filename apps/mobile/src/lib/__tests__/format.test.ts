import { formatCurrency, formatNumber, formatPercent, pnlColor } from '../format';

describe('format helpers', () => {
  it('formats currency with symbol and thousands separators', () => {
    expect(formatCurrency(1234.5)).toBe('$1,234.50');
    expect(formatCurrency(-2416.457)).toBe('-$2,416.46');
    expect(formatCurrency(1000, 'EUR')).toBe('€1,000.00');
    expect(formatCurrency(500, 'AUD')).toBe('AUD 500.00');
  });

  it('formats signed percentages', () => {
    expect(formatPercent(2.5)).toBe('+2.50%');
    expect(formatPercent(-1)).toBe('-1.00%');
    expect(formatPercent(0)).toBe('+0.00%');
  });

  it('trims trailing zeros in numbers', () => {
    expect(formatNumber(10)).toBe('10');
    expect(formatNumber(10.5)).toBe('10.5');
    expect(formatNumber(1234.12)).toBe('1,234.12');
  });

  it('picks gain/loss colors', () => {
    expect(pnlColor(5)).toContain('emerald');
    expect(pnlColor(-5)).toContain('rose');
  });

  it('guards against NaN', () => {
    expect(formatCurrency(NaN)).toBe('$0.00');
    expect(formatPercent(Infinity)).toBe('+0.00%');
  });
});
