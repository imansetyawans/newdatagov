import type { Metadata } from "next";
import { Providers } from "@/app/providers";
import { AppShell } from "@/components/layout/AppShell";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "DataGov",
  description: "Localhost-first data governance MVP"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
