import type { Grade } from '@/lib/types';

interface GradeBadgeProps {
  grade: Grade;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const gradeColors: Record<Grade, string> = {
  A: 'bg-green-500',
  B: 'bg-blue-500',
  C: 'bg-yellow-500',
  D: 'bg-orange-500',
  F: 'bg-red-500',
};

const sizes = {
  sm: 'w-6 h-6 text-xs',
  md: 'w-8 h-8 text-sm',
  lg: 'w-12 h-12 text-xl',
};

export default function GradeBadge({ grade, size = 'md', showLabel = false }: GradeBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={`${gradeColors[grade]} ${sizes[size]} rounded-full flex items-center justify-center text-white font-bold`}
      >
        {grade}
      </span>
      {showLabel && (
        <span className="text-gray-600 dark:text-gray-400 text-sm">Grade</span>
      )}
    </div>
  );
}
