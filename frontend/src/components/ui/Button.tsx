import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "danger";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  icon?: ReactNode;
  isLoading?: boolean;
  loadingText?: string;
};

const variants: Record<ButtonVariant, string> = {
  primary: "border-[var(--color-brand)] bg-[var(--color-brand)] text-white",
  secondary: "border-[var(--color-border)] bg-white text-[var(--color-text-secondary)]",
  danger: "border-[var(--color-danger-border)] bg-white text-[var(--color-danger-text)]"
};

export function Button({
  children,
  className = "",
  disabled,
  icon,
  isLoading = false,
  loadingText,
  variant = "secondary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-8 items-center justify-center gap-2 rounded-[7px] border px-3 text-[13px] font-medium transition duration-150 hover:-translate-y-px disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40 ${variants[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="h-3.5 w-3.5 rounded-full border-2 border-current border-t-transparent animate-datagov-spin" aria-hidden="true" />
      ) : icon ? (
        <span aria-hidden="true">{icon}</span>
      ) : null}
      <span>{isLoading && loadingText ? loadingText : children}</span>
    </button>
  );
}
