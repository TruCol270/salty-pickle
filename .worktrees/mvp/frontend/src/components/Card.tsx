import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
}

export function Card({ children, className = '', title }: CardProps) {
  return (
    <div
      className={`rounded-lg border border-grunge-charcoal bg-grunge-charcoal/80 p-4 shadow-neon-pink/20 backdrop-blur-sm ${className}`}
    >
      {title ? (
        <h3 className="mb-3 font-display text-lg font-bold tracking-wide text-grunge-acid">
          {title}
        </h3>
      ) : null}
      {children}
    </div>
  );
}
