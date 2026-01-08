import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
}

export default function Card({ children, className = '' }: CardProps) {
  return (
    <div
      className={`bg-white rounded-xl border border-warm-200 shadow-soft p-6 ${className}`}
    >
      {children}
    </div>
  );
}
