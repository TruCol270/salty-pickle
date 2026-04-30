import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = '', id, ...rest }: InputProps) {
  const inputId = id || rest.name;
  return (
    <div className="space-y-1">
      {label ? (
        <label htmlFor={inputId} className="text-xs font-semibold uppercase tracking-wider text-grunge-blue">
          {label}
        </label>
      ) : null}
      <input
        id={inputId}
        className={`w-full rounded-md border border-grunge-charcoal bg-grunge-black px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:border-grunge-acid focus:outline-none focus:ring-1 focus:ring-grunge-acid ${className}`}
        {...rest}
      />
      {error ? <p className="text-xs text-grunge-orange">{error}</p> : null}
    </div>
  );
}
