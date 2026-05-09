import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "danger";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variants: Record<ButtonVariant, string> = {
  primary: "border-[var(--color-brand)] bg-[var(--color-brand)] text-white",
  secondary: "border-[var(--color-border)] bg-white text-[var(--color-text-secondary)]",
  danger: "border-[var(--color-danger-border)] bg-white text-[var(--color-danger-text)]"
};

export function Button({ className = "", variant = "secondary", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-8 items-center justify-center rounded-[7px] border px-3 text-[13px] font-medium disabled:cursor-not-allowed disabled:opacity-40 ${variants[variant]} ${className}`}
      {...props}
    />
  );
}

