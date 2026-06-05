import type { ReactNode } from 'react';

type BadgeProps = {
  children?: ReactNode;
  tone?: 'green' | 'gray' | 'orange' | 'red' | 'blue';
};

export function Badge({ children, tone = 'gray' }: BadgeProps) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
