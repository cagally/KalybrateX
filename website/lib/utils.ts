// Client-safe utility functions (no server-only imports)

/**
 * Format cost as USD string
 */
export function formatCost(cost: number): string {
  if (cost < 0.01) {
    return `$${cost.toFixed(4)}`;
  }
  return `$${cost.toFixed(3)}`;
}

/**
 * Format large numbers with commas
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Get grade color class
 */
export function getGradeColor(grade: string): string {
  const colors: Record<string, string> = {
    A: 'bg-grade-A',
    B: 'bg-grade-B',
    C: 'bg-grade-C',
    D: 'bg-grade-D',
    F: 'bg-grade-F',
  };
  return colors[grade] || 'bg-gray-500';
}

/**
 * Get security color class
 */
export function getSecurityColor(grade: string): string {
  const colors: Record<string, string> = {
    secure: 'bg-security-secure',
    warning: 'bg-security-warning',
    fail: 'bg-security-fail',
  };
  return colors[grade] || 'bg-gray-500';
}
