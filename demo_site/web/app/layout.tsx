import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Operations Manager — Live Demo",
  description: "A live preview of your AI Operations Manager.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Material+Icons&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#030712] text-slate-100 antialiased">{children}</body>
    </html>
  );
}
