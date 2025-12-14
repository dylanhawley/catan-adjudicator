import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Catan Rules Q&A',
  description: 'Ask questions about Catan board game rules with verified citations',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

