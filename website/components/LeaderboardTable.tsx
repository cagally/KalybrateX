'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import type { SkillRating, Grade, SecurityGrade } from '@/lib/types';
import GradeBadge from './GradeBadge';
import SecurityBadge from './SecurityBadge';
import { formatCost, formatNumber } from '@/lib/utils';

interface LeaderboardTableProps {
  ratings: SkillRating[];
}

type SortField = 'rank' | 'skill_name' | 'grade' | 'win_rate' | 'security_grade' | 'github_stars';
type SortDirection = 'asc' | 'desc';

export default function LeaderboardTable({ ratings }: LeaderboardTableProps) {
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [gradeFilter, setGradeFilter] = useState<Grade | 'all'>('all');
  const [securityFilter, setSecurityFilter] = useState<SecurityGrade | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredAndSorted = useMemo(() => {
    let result = [...ratings];

    // Filter by grade
    if (gradeFilter !== 'all') {
      result = result.filter(r => r.grade === gradeFilter);
    }

    // Filter by security
    if (securityFilter !== 'all') {
      result = result.filter(r => r.security_grade === securityFilter);
    }

    // Filter by search
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(r =>
        r.skill_name.toLowerCase().includes(term) ||
        r.description?.toLowerCase().includes(term)
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'rank':
          // Use original order (index)
          comparison = ratings.indexOf(a) - ratings.indexOf(b);
          break;
        case 'skill_name':
          comparison = a.skill_name.localeCompare(b.skill_name);
          break;
        case 'grade':
          const gradeOrder = { A: 1, B: 2, C: 3, D: 4, F: 5 };
          comparison = gradeOrder[a.grade] - gradeOrder[b.grade];
          break;
        case 'win_rate':
          comparison = b.win_rate - a.win_rate;
          break;
        case 'security_grade':
          const secOrder = { secure: 1, warning: 2, fail: 3 };
          comparison = secOrder[a.security_grade] - secOrder[b.security_grade];
          break;
        case 'github_stars':
          comparison = b.github_stars - a.github_stars;
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [ratings, sortField, sortDirection, gradeFilter, securityFilter, searchTerm]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <span className="text-gray-400 ml-1">↕</span>;
    return <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div id="leaderboard" className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Search skills..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <select
          value={gradeFilter}
          onChange={(e) => setGradeFilter(e.target.value as Grade | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">All Grades</option>
          <option value="A">Grade A</option>
          <option value="B">Grade B</option>
          <option value="C">Grade C</option>
          <option value="D">Grade D</option>
          <option value="F">Grade F</option>
        </select>
        <select
          value={securityFilter}
          onChange={(e) => setSecurityFilter(e.target.value as SecurityGrade | 'all')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="all">All Security</option>
          <option value="secure">Secure</option>
          <option value="warning">Warning</option>
          <option value="fail">Fail</option>
        </select>
      </div>

      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th
                onClick={() => handleSort('rank')}
                className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200"
              >
                Rank <SortIcon field="rank" />
              </th>
              <th
                onClick={() => handleSort('skill_name')}
                className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200"
              >
                Skill <SortIcon field="skill_name" />
              </th>
              <th
                onClick={() => handleSort('grade')}
                className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200"
              >
                Grade <SortIcon field="grade" />
              </th>
              <th
                onClick={() => handleSort('win_rate')}
                className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200"
              >
                Win Rate <SortIcon field="win_rate" />
              </th>
              <th
                onClick={() => handleSort('security_grade')}
                className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200"
              >
                Security <SortIcon field="security_grade" />
              </th>
              <th
                onClick={() => handleSort('github_stars')}
                className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200"
              >
                Stars <SortIcon field="github_stars" />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                Cost
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSorted.map((skill, index) => (
              <tr
                key={skill.skill_name}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition"
              >
                <td className="px-4 py-4 text-gray-500 dark:text-gray-400">
                  {sortField === 'rank' ? index + 1 : '-'}
                </td>
                <td className="px-4 py-4">
                  <Link
                    href={`/skill/${skill.skill_name}`}
                    className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                  >
                    {skill.skill_name}
                  </Link>
                </td>
                <td className="px-4 py-4">
                  <GradeBadge grade={skill.grade} size="sm" />
                </td>
                <td className="px-4 py-4 text-gray-700 dark:text-gray-300">
                  {skill.win_rate.toFixed(0)}%
                </td>
                <td className="px-4 py-4">
                  <SecurityBadge grade={skill.security_grade} size="sm" />
                </td>
                <td className="px-4 py-4 text-gray-700 dark:text-gray-300">
                  {formatNumber(skill.github_stars)}
                </td>
                <td className="px-4 py-4 text-gray-500 dark:text-gray-400 text-sm">
                  {formatCost(skill.cost_per_use_usd)}/use
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-4">
        {filteredAndSorted.map((skill, index) => (
          <Link
            key={skill.skill_name}
            href={`/skill/${skill.skill_name}`}
            className="block p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-sm">#{index + 1}</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {skill.skill_name}
                </span>
              </div>
              <GradeBadge grade={skill.grade} size="sm" />
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {skill.win_rate.toFixed(0)}% win
              </span>
              <SecurityBadge grade={skill.security_grade} size="sm" />
              <span className="text-sm text-gray-500">
                ★ {formatNumber(skill.github_stars)}
              </span>
            </div>
          </Link>
        ))}
      </div>

      {/* Empty state */}
      {filteredAndSorted.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No skills match your filters. Try adjusting your search.
          </p>
        </div>
      )}

      {/* Results count */}
      <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
        Showing {filteredAndSorted.length} of {ratings.length} skills
      </div>
    </div>
  );
}
