// Types for KalybrateX website

export type Grade = 'A' | 'B' | 'C' | 'D' | 'F';
export type SecurityGrade = 'secure' | 'warning' | 'fail';
export type SkillCategory = 'file_artifact' | 'code_generation' | 'configuration' | 'advisory';

export interface SkillRating {
  skill_name: string;
  quality_grade: Grade;
  quality_win_rate: number;
  wins: number;
  losses: number;
  ties: number;
  security_grade: SecurityGrade;
  security_issues_count: number;
  avg_tokens_per_use: number;
  cost_per_use_usd: number;
  avg_baseline_tokens: number;
  baseline_cost_usd: number;
  total_comparisons: number;
  scored_at: string;
  github_url: string;
  github_stars: number;
  description: string;
  // Combined fields (may not exist for all skills)
  grade: Grade;
  win_rate: number;
  execution_grade?: Grade;
  execution_win_rate?: number;
  combined_score?: number;
  final_grade?: Grade;
  category?: SkillCategory;
  execution_wins?: number;
  execution_losses?: number;
  execution_ties?: number;
}

export interface Leaderboard {
  generated_at: string;
  total_skills: number;
  ratings: SkillRating[];
}

export interface Comparison {
  prompt: string;
  baseline_response: string;
  skill_response: string;
  verdict: 'skill' | 'baseline' | 'tie';
  reasoning: string;
  baseline_tokens: number;
  skill_tokens: number;
  position_a: 'baseline' | 'skill';
  position_b: 'baseline' | 'skill';
  judge_model: string;
  judged_at: string;
}

export interface SkillSummary {
  skill_name: string;
  quality_grade: Grade;
  quality_win_rate: number;
  security_grade: SecurityGrade;
  security_issues_count: number;
  total_comparisons: number;
  prompt_count: number;
  verdict_breakdown: {
    skill_wins: number;
    baseline_wins: number;
    ties: number;
  };
  avg_tokens_per_use: number;
  cost_per_use_usd: number;
  evaluated_at: string;
  execution_grade?: Grade;
  execution_win_rate?: number;
  category?: SkillCategory;
  grade: Grade;
  win_rate: number;
}

export interface SecurityIssue {
  category: string;
  severity: string;
  description: string;
  evidence: string;
}

export interface SecurityResult {
  skill_name: string;
  grade: SecurityGrade;
  issues: SecurityIssue[];
  analysis: string;
  analyzed_at: string;
  model_used: string;
  tokens_used: number;
}

export interface SkillDetail {
  summary: SkillSummary;
  comparison: Comparison;
  security?: SecurityResult;
}
