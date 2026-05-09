/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-ui)"],
        mono: ["var(--font-mono)"]
      },
      colors: {
        brand: "var(--color-brand)",
        surface: "var(--color-surface)",
        border: "var(--color-border)"
      }
    }
  },
  plugins: []
};

