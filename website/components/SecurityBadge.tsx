import type { SecurityGrade } from '@/lib/types';

interface SecurityBadgeProps {
  grade: SecurityGrade;
  size?: 'sm' | 'md';
}

const securityColors: Record<SecurityGrade, string> = {
  secure: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  warning: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  fail: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const securityIcons: Record<SecurityGrade, string> = {
  secure: '✓',
  warning: '⚠',
  fail: '✗',
};

const sizes = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
};

export default function SecurityBadge({ grade, size = 'md' }: SecurityBadgeProps) {
  return (
    <span
      className={`${securityColors[grade]} ${sizes[size]} rounded-full font-medium inline-flex items-center gap-1`}
    >
      <span>{securityIcons[grade]}</span>
      <span className="capitalize">{grade}</span>
    </span>
  );
}
