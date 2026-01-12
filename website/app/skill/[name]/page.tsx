import { notFound } from 'next/navigation';
import Link from 'next/link';
import type { Metadata } from 'next';
import { getAllSkillNames, getSkillRating, getSkillDetail } from '@/lib/data';
import { formatCost, formatNumber } from '@/lib/utils';
import GradeBadge from '@/components/GradeBadge';
import SecurityBadge from '@/components/SecurityBadge';
import ComparisonViewer from '@/components/ComparisonViewer';
import ShareButtons from '@/components/ShareButtons';

interface PageProps {
  params: { name: string };
}

// Generate static paths for all skills
export async function generateStaticParams() {
  const names = getAllSkillNames();
  return names.map((name) => ({ name }));
}

// Dynamic metadata
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const rating = getSkillRating(params.name);
  if (!rating) return { title: 'Skill Not Found' };

  return {
    title: `${rating.skill_name} Skill Rating - ${rating.grade} Grade | KalybrateX`,
    description: `${rating.skill_name} scores ${rating.win_rate.toFixed(0)}% in our A/B tests. ${rating.description || ''}`,
    openGraph: {
      title: `${rating.skill_name} - ${rating.grade} Grade`,
      description: `Win rate: ${rating.win_rate.toFixed(0)}% | ${rating.description || ''}`,
    },
  };
}

export default function SkillDetailPage({ params }: PageProps) {
  const rating = getSkillRating(params.name);
  const detail = getSkillDetail(params.name);

  if (!rating || !detail) {
    notFound();
  }

  const { summary, comparison, security } = detail;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="text-sm mb-6">
        <Link href="/" className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
          Leaderboard
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900 dark:text-white">{rating.skill_name}</span>
      </nav>

      {/* Hero Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-4 mb-4">
              <GradeBadge grade={rating.grade} size="lg" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {rating.skill_name}
                </h1>
                <p className="text-lg text-green-600 dark:text-green-400">
                  {rating.win_rate.toFixed(0)}% better than baseline
                </p>
              </div>
            </div>

            {rating.description && (
              <p className="text-gray-600 dark:text-gray-400 mb-4 max-w-2xl">
                {rating.description}
              </p>
            )}

            <div className="flex flex-wrap items-center gap-4">
              <a
                href={rating.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                </svg>
                View SKILL.md
              </a>
              <span className="text-gray-500 dark:text-gray-400">
                ★ {formatNumber(rating.github_stars)} stars
              </span>
              <SecurityBadge grade={rating.security_grade} />
              <Link
                href="/methodology"
                className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              >
                How was this rated? →
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Quality</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {rating.quality_grade} ({rating.quality_win_rate.toFixed(0)}%)
          </p>
        </div>
        {rating.execution_grade && (
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Execution</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">
              {rating.execution_grade} ({rating.execution_win_rate?.toFixed(0)}%)
            </p>
          </div>
        )}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Security</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white capitalize">
            {rating.security_grade}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Cost/Use</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {formatCost(rating.cost_per_use_usd)}
          </p>
        </div>
      </div>

      {/* Security Issues */}
      {security && security.issues.length > 0 && (
        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800 p-4 mb-8">
          <h3 className="font-medium text-orange-800 dark:text-orange-200 mb-3">
            Security Issues ({security.issues.length})
          </h3>
          <ul className="space-y-2">
            {security.issues.map((issue, idx) => (
              <li key={idx} className="text-sm text-orange-700 dark:text-orange-300">
                <span className="font-medium">{issue.severity}:</span> {issue.description}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Evidence Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            See the Evidence
          </h2>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            1 of {summary.total_comparisons} comparisons
          </span>
        </div>
        <ComparisonViewer comparison={comparison} defaultExpanded={true} />
      </div>

      {/* Share */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-8 border-t border-gray-200 dark:border-gray-700">
        <ShareButtons
          title={`${rating.skill_name} Skill Rating`}
          text={`${rating.skill_name} scored ${rating.grade} grade (${rating.win_rate.toFixed(0)}% win rate) on KalybrateX`}
        />
        <a
          href={`https://github.com/cagally/KalybrateX/tree/main/data/evaluations/${rating.skill_name}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          View all evidence (JSON) →
        </a>
      </div>
    </div>
  );
}
