import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost';

const variants: Record<Variant, string> = {
  primary:
    'bg-grunge-acid text-grunge-black font-bold shadow-neon-acid hover:brightness-110 active:scale-[0.98]',
  secondary:
    'bg-grunge-charcoal text-grunge-acid border border-grunge-acid/40 hover:bg-grunge-black',
  ghost: 'bg-transparent text-grunge-blue hover:underline',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: Variant;
}

export function Button({
  children,
  variant = 'primary',
  className = '',
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm transition-all ${variants[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
