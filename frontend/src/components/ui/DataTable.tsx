import type { ReactNode } from "react";

type DataTableProps = {
  headers: string[];
  children: ReactNode;
  caption?: string;
};

export function DataTable({ headers, children, caption }: DataTableProps) {
  return (
    <div className="overflow-x-auto rounded-[8px] border border-[var(--color-border)] bg-white">
      <table className="min-w-[1120px] table-auto border-collapse">
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            {headers.map((header) => (
              <th
                key={header}
                scope="col"
                className="px-4 py-3 text-left text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
