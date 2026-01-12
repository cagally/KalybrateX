import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'KalybrateX - AI Skill Ratings | Find Skills That Actually Work',
  description:
    'Independent ratings of AI agent skills. We test with A/B comparisons to show which skills make Claude better.',
  keywords: ['AI skills', 'Claude', 'skill ratings', 'agent skills', 'LLM'],
  authors: [{ name: 'KalybrateX' }],
  openGraph: {
    title: 'KalybrateX - AI Skill Ratings',
    description: 'Find AI skills that actually work. Rated with A/B testing.',
    type: 'website',
    locale: 'en_US',
    siteName: 'KalybrateX',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'KalybrateX - AI Skill Ratings',
    description: 'Find AI skills that actually work. Rated with A/B testing.',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen flex flex-col`}>
        <Nav />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
