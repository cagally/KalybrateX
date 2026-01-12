'use client';

import { useState } from 'react';
import type { Comparison } from '@/lib/types';

interface ComparisonViewerProps {
  comparison: Comparison;
  defaultExpanded?: boolean;
}

export default function ComparisonViewer({ comparison, defaultExpanded = true }: ComparisonViewerProps) {
  const [showBaseline, setShowBaseline] = useState(defaultExpanded);
  const [showSkill, setShowSkill] = useState(defaultExpanded);

  const verdictColors = {
    skill: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    baseline: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    tie: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  };

  const verdictLabels = {
    skill: 'Skill Won',
    baseline: 'Baseline Won',
    tie: 'Tie',
  };

  return (
    <div className="space-y-6">
      {/* Prompt */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
        <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
          Prompt
        </h4>
        <p className="text-gray-800 dark:text-gray-200">{comparison.prompt}</p>
      </div>

      {/* Responses side by side on desktop, stacked on mobile */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Baseline */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setShowBaseline(!showBaseline)}
            className="w-full flex items-center justify-between p-4 text-left"
          >
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-700 dark:text-gray-300">
                Baseline Response
              </span>
              <span className="text-xs text-gray-500">
                (without skill)
              </span>
            </div>
            <span className="text-gray-400">{showBaseline ? '−' : '+'}</span>
          </button>
          {showBaseline && (
            <div className="px-4 pb-4">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 p-4 rounded border border-gray-200 dark:border-gray-700 max-h-96 overflow-auto">
                {comparison.baseline_response}
              </pre>
              <p className="text-xs text-gray-500 mt-2">
                {comparison.baseline_tokens.toLocaleString()} tokens
              </p>
            </div>
          )}
        </div>

        {/* Skill */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setShowSkill(!showSkill)}
            className="w-full flex items-center justify-between p-4 text-left"
          >
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-700 dark:text-gray-300">
                Skill Response
              </span>
              <span className="text-xs text-gray-500">
                (with SKILL.md)
              </span>
            </div>
            <span className="text-gray-400">{showSkill ? '−' : '+'}</span>
          </button>
          {showSkill && (
            <div className="px-4 pb-4">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 p-4 rounded border border-gray-200 dark:border-gray-700 max-h-96 overflow-auto">
                {comparison.skill_response}
              </pre>
              <p className="text-xs text-gray-500 mt-2">
                {comparison.skill_tokens.toLocaleString()} tokens
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Verdict */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-3 mb-3">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${verdictColors[comparison.verdict]}`}>
            {verdictLabels[comparison.verdict]}
          </span>
          <span className="text-xs text-gray-500">
            Judged by {comparison.judge_model}
          </span>
        </div>
        <p className="text-gray-700 dark:text-gray-300 text-sm">
          {comparison.reasoning}
        </p>
      </div>
    </div>
  );
}
