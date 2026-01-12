import type { Leaderboard, SkillRating, SkillDetail, Comparison, SkillSummary, SecurityResult } from './types';

// Note: These functions run only on the server during build
// The fs imports happen at runtime on the server only

/**
 * Get the full leaderboard data
 */
export function getLeaderboard(): Leaderboard {
  // Dynamic require to avoid client-side bundling
  const fs = require('fs');
  const path = require('path');
  const dataDir = path.join(process.cwd(), '..', 'data');
  const filePath = path.join(dataDir, 'leaderboard.json');
  const content = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(content);
}

/**
 * Get sorted leaderboard ratings
 */
export function getSortedRatings(): SkillRating[] {
  const leaderboard = getLeaderboard();
  // Already sorted by grade/win_rate in the JSON, but we can re-sort if needed
  return leaderboard.ratings;
}

/**
 * Get all skill names for static path generation
 */
export function getAllSkillNames(): string[] {
  const leaderboard = getLeaderboard();
  return leaderboard.ratings.map(r => r.skill_name);
}

/**
 * Get a specific skill's rating from leaderboard
 */
export function getSkillRating(name: string): SkillRating | undefined {
  const leaderboard = getLeaderboard();
  return leaderboard.ratings.find(r => r.skill_name === name);
}

/**
 * Get detailed skill data including summary and sample comparison
 */
export function getSkillDetail(name: string): SkillDetail | null {
  const fs = require('fs');
  const path = require('path');
  const dataDir = path.join(process.cwd(), '..', 'data');

  try {
    const evalDir = path.join(dataDir, 'evaluations', name);

    // Load summary
    const summaryPath = path.join(evalDir, 'summary.json');
    const summaryContent = fs.readFileSync(summaryPath, 'utf-8');
    const summary: SkillSummary = JSON.parse(summaryContent);

    // Load first comparison as sample
    const comparisonPath = path.join(evalDir, 'comparisons', '0.json');
    const comparisonContent = fs.readFileSync(comparisonPath, 'utf-8');
    const comparison: Comparison = JSON.parse(comparisonContent);

    // Try to load security data
    let security: SecurityResult | undefined;
    try {
      const securityPath = path.join(evalDir, 'security.json');
      const securityContent = fs.readFileSync(securityPath, 'utf-8');
      security = JSON.parse(securityContent);
    } catch {
      // Security data may not exist
    }

    return { summary, comparison, security };
  } catch (error) {
    console.error(`Failed to load skill detail for ${name}:`, error);
    return null;
  }
}

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
