import Hero from '@/components/Hero';
import LeaderboardTable from '@/components/LeaderboardTable';
import { getSortedRatings, getLeaderboard } from '@/lib/data';
import Link from 'next/link';

export default function HomePage() {
  const ratings = getSortedRatings();
  const leaderboard = getLeaderboard();

  return (
    <div>
      <Hero />

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Skill Leaderboard
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {leaderboard.total_skills} skills rated &middot; Updated{' '}
              {new Date(leaderboard.generated_at).toLocaleDateString()}
            </p>
          </div>
          <Link
            href="/methodology"
            className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
          >
            How do we rate? →
          </Link>
        </div>

        <LeaderboardTable ratings={ratings} />
      </section>
    </div>
  );
}
