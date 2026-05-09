"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="grid min-h-[60vh] place-items-center">
      <section className="grid max-w-md gap-3 rounded-[8px] border border-[var(--color-border)] bg-white p-6">
        <h1 className="m-0 text-[20px] font-medium">Something went wrong</h1>
        <p className="m-0 text-[13px] text-[var(--color-text-secondary)]">
          The page could not finish loading. Try again after checking the backend connection.
        </p>
        <Button type="button" variant="primary" onClick={reset}>
          Try again
        </Button>
      </section>
    </div>
  );
}
