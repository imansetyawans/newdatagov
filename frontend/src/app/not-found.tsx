import Link from "next/link";

export default function NotFound() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <section className="grid max-w-md gap-3 rounded-[8px] border border-[var(--color-border)] bg-white p-6">
        <h1 className="m-0 text-[20px] font-medium">Page not found</h1>
        <p className="m-0 text-[13px] text-[var(--color-text-secondary)]">
          The requested page is not available in this DataGov workspace.
        </p>
        <Link
          href="/"
          className="inline-flex min-h-8 w-fit items-center rounded-[7px] bg-[var(--color-brand)] px-3 text-[13px] font-medium text-white"
        >
          Back to dashboard
        </Link>
      </section>
    </div>
  );
}
